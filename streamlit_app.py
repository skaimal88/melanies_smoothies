# Import python packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# App title and intro
st.title(f":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("""Choose the fruits you want in your custom Smoothie!.""")

# User input: Name on smoothie
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write("The name on your Smoothie will be:", name_on_order)

# Snowflake connection and session
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit data from Snowflake
my_data_frame = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_data_frame.to_pandas()

# Filter out rows with invalid SEARCH_ON values
pd_df = pd_df[pd_df['SEARCH_ON'].notna() & (pd_df['SEARCH_ON'].str.strip() != '')]

# Extract fruit options for selection
fruit_options = pd_df['FRUIT_NAME'].tolist()

# Multiselect for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options,
    max_selections=5
)

# Initialize ingredient string
ingredients_string = ''
if ingredients_list:
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ', '

        # Get search value
        match_row = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen]
        search_on = match_row['SEARCH_ON'].values[0]

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # Show spinner while fetching
        with st.spinner(f"Fetching info for {fruit_chosen}..."):
            try:
                smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
                smoothiefroot_response.raise_for_status()
                data = smoothiefroot_response.json()

                # Convert dict to DataFrame and display
                data_df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])
                data_df.index.name = 'Nutrition Info'
                st.dataframe(data_df, use_container_width=True)

            except requests.RequestException as e:
                st.warning(f"Could not fetch info for {fruit_chosen}. Error: {e}")

# Remove trailing comma
ingredients_string = ingredients_string.rstrip(', ')

# Prepare SQL insert statement
my_insert_stmt = f"""
    insert into smoothies.public.orders(ingredients, name_on_order)
    values (%s, %s)
"""

# Submit order
if ingredients_list and name_on_order:
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        try:
            session.cursor().execute(my_insert_stmt, (ingredients_string, name_on_order))
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Order submission failed. Error: {e}")
else:
    st.info("Enter your name and select ingredients to enable the order button.")
