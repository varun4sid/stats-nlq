import streamlit as st
import pandas as pd
from nlp_engine.pipeline import process_query
from nlp_engine.query_builder import generate_and_execute_sql
import os

st.set_page_config(page_title="StatMuse Clone MVP", layout="centered")

st.title("🏀 StatMuse Mini")
st.markdown("Ask natural language queries about NBA player and team stats.")

st.info("Example queries:\n- **LeBron James points last game**\n- **Steph Curry statline last 5 games**\n- **Lakers total rebounds last 3 games**\n- **Who scored the most points for the Warriors last game?**")

query = st.text_input("Enter your basketball query:")

if st.button("Search") or query:
    if query:
        with st.spinner("Processing NLP..."):
            parsed = process_query(query)
            
        if "error" in parsed:
            st.error(parsed["error"])
            if "confidence" in parsed:
                st.write(f"Confidence: {parsed['confidence']:.2f}")
        else:
            st.write(f"**Intent:** {parsed['intent']} (Confidence: {parsed['confidence']:.2f})")
            st.write(f"**Extracted Entities:** {parsed['entities']}")
            
            with st.spinner("Executing SQL..."):
                result = generate_and_execute_sql(parsed)
                
            if "error" in result:
                st.error(result["error"])
                if "query" in result:
                    st.code(result["query"], language="sql", wrap_lines=True)
            else:
                st.success("Query Executed Successfully!")
                st.code(result["query"], language="sql", wrap_lines=True)
                df = result["dataframe"]
                if df.empty:
                    st.warning("No data found for this query.")
                else:
                    st.dataframe(df, hide_index=True)
