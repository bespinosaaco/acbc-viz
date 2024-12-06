import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import pandas as pd
import io
import plotly.graph_objects as go
import numpy as np
import hmac

st.set_page_config(page_title="AC/BC Visualize",layout="wide")

# Connecting to the cloud
NEXTCLOUD_URL = st.secrets["nextcloud"]["NEXTCLOUD_URL"]
USERNAME = st.secrets["nextcloud"]["username"]
PASSWORD = st.secrets["nextcloud"]["next_cloudpass"]

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["nextcloud"]["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.title("Welcome to AC/BC 🦦")
    st.write(''' ### Insert group's password to access''')
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

@st.cache_data
def get_csv_file_as_dataframe(file_path):
    url = f"{NEXTCLOUD_URL}{file_path}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))
            return df
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to Load the master: {e}")
        return []

# Function to list files in the specified folder on NextCloud
@st.cache_data
def list_nextcloud_folder_files(folder_path="/specific-folder"):
    url = f"{NEXTCLOUD_URL}{folder_path}/"
    try:
        response = requests.request("PROPFIND", url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        response.raise_for_status()  # Raise an error for bad responses
        file_list = []
        if response.status_code == 207:
            # Parse XML response to get file and folder names
            root = ET.fromstring(response.text)
            namespace = {'d': 'DAV:'}

            for response in root.findall("d:response", namespace):
                href = response.find("d:href", namespace).text
                if href.endswith('/'):
                    folder_name = href.split('/')[-2]
                    if folder_name != folder_path.strip('/'):
                        file_list.append(folder_name)
                else:
                    file_name = href.split('/')[-1]
                    file_list.append(file_name)
        return file_list
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to list files: {e}")
        return []

# Function to get data as a DataFrame
@st.cache_data
def get_dpt_as_dataframe(file_path):
    url = f"{NEXTCLOUD_URL}{file_path}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        response.raise_for_status()  # Raise an error for bad responses
        dpt = response.content.decode('utf-8')
        df = pd.read_table(io.StringIO(dpt), header=None, names=['Wavenumber', 'Intensity'], delimiter=',')
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading file: {e}")
        return None

# Function to load and normalize data
# @st.cache_data
def load_and_normalize_data(choices):
    sample_dic = {}
    for i in choices:
        df = get_dpt_as_dataframe(f'/processed/{i}')
        if df is not None:
            sample_dic[i] = Norm(df)
    st.write("Loaded and normalized!")
    return sample_dic

# Normalization function
def Norm(ATR, min_value=0, max_value=1):
    min_val = ATR.iloc[:, 1].min()
    max_val = ATR.iloc[:, 1].max()
    ATR['norm'] = ((ATR.iloc[:, 1] - min_val) / (max_val - min_val)) * (max_value - min_value) + min_value
    return ATR


############################# The app begins here!!! #########################################################################

# Set page configuration
st.logo('logo.png',link = None,size="large")  #Add a link here to TCA

def Dashboard():
    st.title("Welcome to AC/BC Viz 🦦!")
    st.caption("Scroll down to see all the interactives and downloadables graphics")

    with st.spinner('Connecting to Brian NextCloud...'):
        if 'master' in st.session_state:
            master = st.session_state['master']
        else:
            master = get_csv_file_as_dataframe("/master.csv")
            st.session_state['master'] = master
        file_list = list_nextcloud_folder_files("/processed")

    col_reload = st.columns([1, 0.1])
    with col_reload[0]:
        st.write('Connected to Brian NextCloud')
    with col_reload[1]:
        with st.spinner('Reloading'):
            if st.button('🔄️'):
                get_csv_file_as_dataframe.clear()
                master = get_csv_file_as_dataframe("/master.csv")
                st.session_state['master'] = master
        # This is to check if the reload button is working
        #         st.session_state['reload_count'] = st.session_state.get('reload_count', 0) + 1
        #
        # st.write(f"Reload count: {st.session_state.get('reload_count', 0)}")

    st.write('''
    ### Master Biochar Inventory 📖
    ''')
    st.caption('This is the Biochar Inventory. You can sort, search, expand and download')
    st.dataframe(master,use_container_width=True)

    st.write('''
        ---
        ### Visualize information from the selected samples 👇 
        ---
        ''')
    par1,par2 =st.columns((1,1))
    with par1:
        choice = st.multiselect('Select sample(s)', options=master['Code'], placeholder='Code',
                            help='Select the samples you wish to compare')
    with par2:
        param = st.selectbox('Parameter', options=['BET', 'pH', 'Yield', 'pore size', 'pore volume'],
                         help='Select one of the parameters',
                         placeholder='Parameter')

    col1, col2, col3 = st.columns((1,2,3))
    col4,col5 =st.columns((1,1))
    if choice and param:
        with col1:
            st.dataframe(master[['Code',param]][master['Code'].isin(choice)],
                         use_container_width=True)
        with col2:
            st.write(f'''
            ### **{param} Method**  
            Some description of the methodology used to record this data.  
            Step-by-step:  
            1. This is step 1  
            2. This is step 2
            ''')
        with col3:
            fig = go.Figure(data=[
                go.Bar(name='Sample Data', x=choice, y=master[param][master['Code'].isin(choice)])
            ])

            fig.update_layout(
                title=f'Sample by {param}',
                xaxis_title='Sample',
                yaxis_title=f'{param}',
                template='plotly_white'  # Optional: set the background to white for better readability
            )
            st.plotly_chart(fig,use_container_width=True)

        with col4:
            df = master[['Code','%C','%H','%N','%O']][master['Code'].isin(choice)]
            df['Other'] = 100 - df[['%C','%H','%N','%O']].sum(axis=1)
            st.caption("The element percentage was input by me. No real data")
            # Create stacked percentage bar graph
            fig = go.Figure()

            for element in ['%C', '%H', '%N', '%O', 'Other']:
                fig.add_trace(go.Bar(
                    x=df['Code'],
                    y=df[element],
                    name=element,
                    text=df[element].apply(lambda x: f'{x:.2f}%'),
                    textposition='auto'
                ))

            # Update layout
            fig.update_layout(
                barmode='stack',
                title='Elemental Analysis Composition',
                xaxis_title='Sample',
                yaxis_title='Percentage (%)',
            )
            st.plotly_chart(fig,use_container_width=True)
    else:
        st.warning('Select the samples and parameters on the sidebar 👆')



    st.write(r'''
    ---
    ### Adsorption, SSA, $(O+N)/C$  
    ''')
    st.warning('Simulated data for displaying')
    # Generate random data for the 3D scatter plot
    num_points = 100
    x = np.random.uniform(10, 300, num_points)
    y = np.random.uniform(10, 300, num_points)
    z = np.random.uniform(10, 300, num_points)

    # Create a 3D scatter plot with Plotly
    # Create labels for each data point
    labels = [f"acbc{i}: ({z[i]:.2f}, {x[i]:.2f}, {y[i]:.2f})" for i in range(num_points)]
    fig = go.Figure(data=[go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        marker=dict(
            size=5,
            color=z,  # Color by z values
            colorscale='Viridis',
            opacity=0.8),
        text=labels,  # Add labels for hover
        hoverinfo='text'  # Display only the text on hover

    )])

    # Customize layout
    fig.update_layout(
        paper_bgcolor="rgba(230, 230, 230, 0.8)",
        width=800,
        height=800,
        scene=dict(
        xaxis_title='(N+O)/C',
        yaxis_title='SSA',
        zaxis_title='Adsorption',
    ))

    # 3D scatter plot
    st.plotly_chart(fig,use_container_width=True)

    st.write('''
    ---
    ### Infrared spectroscopy  
    ''')
    st.warning("Brian's data. Not the one in the master spreadsheet yet! ⚒️")

    # Load data based on selection
    sample_dic = {}
    option_c = None
    choice = file_list
    sample_dic = load_and_normalize_data(choice)#
    y = 'Intensity'
    on = st.toggle("Plot Normalized")

    if on:
        y = 'norm'
    fig = go.Figure()
    for i in sample_dic.keys():
        fig.add_trace(go.Scatter(x=sample_dic[i]['Wavenumber'], y=sample_dic[i][y],
                                 mode='lines', name=i[:-4]))

    fig.update_layout(
        xaxis=dict(range=[4000, 400]),
        title='ATR-FTIR',
        xaxis_title='Wavelength',
        yaxis_title='Intensity (a.u)',
        width=1200,
        height=800
    )

    st.plotly_chart(fig, use_container_width=True)

pg = st.navigation([st.Page(Dashboard),st.Page("docs.py",title="Documentation")])
pg.run()