import streamlit as st
from streamlit import divider

# Here the page begins
st.title("AC/BC 🦦")
st.caption("Atlantic Canada Biochar Project")
st.header("About US!",divider='green')

st.write('''### Transformative Climate Action''')
st.write("Made by Brian Espinosa Acosta")


st.header("Data Management Tips",divider = "green")
st.markdown('''
### Data file naming:  
ProjectName_instrument_date(yyyymmdd)_ResearcherSampleCode_test#/letter.format  
E.g. ACBC_IR_20240906_BEA001_1.dpt  
:red[**Note**]: ACBC = Atlantic Canada Biochar, IR = infrared, BEA = Brian Espinosa Acosta  
The test number "_1" will need to count with independent descriptions in the researcher lab notebook:  
* "Test number _1 was a 36 scans infrared spectrum"  
* "Test number _2 was a 256 scans infrared spectrum"  

### Instrument data structure:  
- IR: 2-columns, wavenumber(cm-1) | absorption intensity (a.u)  
- PXRD: 2-columns, 2theta degree | Peak Intensity  
- CHNO: 4-columns, C% | H% | N% | O%  
- ICP-OES: 6-columns, element | ppm | 1sd | wt% | RSD (%) | cor.-coeff  
- EDS: 2-columns, Energy (keV) | Intensity (a.u)  
- PA: ?  
- TGA-MS:  
1. TGA: 2-columns, Temperature (oC) | Mass Loss (mg)  
2. MS: 2-columns, mass-to-charge (m/z) | Relative Abundance (%)  
- pH: single digit"
            ''')