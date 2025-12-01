import streamlit as st 

st.set_page_config(layout="wide", page_title="Findings", page_icon="📊")

st.markdown("""
    <style>
        .top-banner {
            width: 100%;
            background-color: #C8DAB9;
            padding: 25px 0;
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            color: black;
            border-radius: 6px;
            margin-bottom: 25px;
        }
        /* Section container */
        .sage-box {
            background-color: #E6F0D9;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }

        /* Styled subheaders inside columns */
        .soft-subheader {
            background-color: #E6F0D9;  /* Lighter sage green */
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        /* Styled sub-subheader */
        .soft-subsubheader {
            background-color:#E6F0D9;
            padding:10px;
            border-radius:10px;
            text-align:left;
            font-size:17px;
            font-weight:500;
            color:#3a3a3a;
            margin-top:5px;
            margin-left:10px;
        }
        /* Image border */
        .sage-image {
            border-radius: 10px;
            border: 3px solid #C8DAB9;
        }
    </style>
    <div class="top-banner">
        Trends and Findings in Our Data
    </div>
""", unsafe_allow_html=True)


st.write("""
We analyzed data from the FBI's Annual Internet Crime Data Reports from 2019 - 2024, and studied the most popular fraud schemes that target people 60 years and older. This data allows us to learn which fraud types to warn this group of people about to help midigate the amount of money lost each year due to fraud in this age bracket. 

**Findings for 60+ consumers**
- Top states where fraud occurs 
- Common types of scams targeting older adults
- Trends over time
""")

# ------ First Finding ------
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("<div class='soft-subheader'>Common Types of Scams</div>", unsafe_allow_html=True)
    st.write("""
       We found the top 5 types of scams targeted towards older adults were:
             - 
             -
             -
             -
             -

        These findings educate adults in American on what current fraudulent activity typically looks like and helps them to avoid falling victim.
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # FIX IMAGE IT IS BLURRY
    st.image("imagesForSL/step1.png", width=550, caption="One part of the PDF data we are scraping.")

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ------ Second Finding ------
col3, col4 = st.columns([1,1])

with col3:
    # ADD IMAGE
    st.image("imagesForSL/step1.png", width=550, caption="One part of the PDF data we are scraping.")

with col4:
    st.markdown("<div class='soft-subheader'>Top States Where Fraud Occurs </div>", unsafe_allow_html=True)

    st.markdown ("""
        This map shows the top states, by color, which have the highest amount of fraud cases between 2022 and 2024. The warming color a state is, the more fraud that has occured.
    """)


# ------ Third Finding ------
col5, col6 = st.columns([1, 1])

with col5:
    st.markdown("<div class='soft-subheader'>Trends Over Time</div>", unsafe_allow_html=True)
    st.write("""
        Through our analysis, we have found the amount of fraud cases to be

    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    # FIX IMAGE IT IS BLURRY
    st.image("imagesForSL/step1.png", width=550, caption="One part of the PDF data we are scraping.")

st.markdown("<div class='thin-line'></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
