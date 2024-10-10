import streamlit as st

# Initialize connection using the credentials from `secrets.toml`
conn = st.connection('apibd06', type='sql')

# Perform query
df = conn.query('SELECT * from data_coralsol_dafor LIMIT 10;', ttl=600)

# Print results
for row in df.itertuples():
    st.write(f"{row.Locality_id}  ")