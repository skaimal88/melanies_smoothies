import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

st.title(f":cup_with_straw: Customize Your Smoothie!:cup_with_straw:")
st.write("""Choose the fruits you want in your custom Smoothie!.""")
name_on_order = st.text_input('Name on Smoothie:')
st.write("The name on your Smoothie will be:", name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()

my_data_frame = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
#st.dataframe(data=my_data_frame, use_container_width=True)
#st.stop()

# Convert the Snowpark Dataframe to a Pandas DF so we can use the LOC function
pd_df = my_data_frame.to_pandas()
# st.dataframe(pd_df)
# st.stop()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:'
    , my_data_frame
    , max_selections = 5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        search_on=pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        #st.write('The search value for ', fruit_chosen,' is ', search_on, '.')
      
        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
        fv_df =st.dataframe(data=fruityvice_response.json(),use_container_width=True)
        #smoothiefroot_response = requests.get("www.smoothiefroot.com/api/fruit/" + search_on)
        #sf_df =st.dataframe(data=smoothiefroot_response.json(),use_container_width=True)
    
    #st.write(ingredients_string) 

    
    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
            values ('""" + ingredients_string + """','"""+name_on_order+"""')"""

    #st.write(my_insert_stmt)
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()

        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
