# import all the library for the project
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load Titanic dataset
@st.cache
def load_data():
    data = pd.read_csv(r'C:\Users\bmittipa\Documents\Vodafone\PrakashSenapati\Python_Learning\Week5_EDA\Titanic_EDA\titanic_dataset.csv')
    return data

data = load_data()

# Title and description
st.title('Exploratory Data Analysis of Titanic Dataset')
st.write('This is an EDA on the Titanic dataset.')
st.write('First few rows of the dataset:')
st.write(data.head())

# Data Cleaning Section
st.subheader('Missing Values')
missing_data = data.isnull().sum()
st.write(missing_data)

if st.checkbox('Fill missing Age with median'):
    data['Age'].fillna(data['Age'].median(), inplace=True)

if st.checkbox('Fill missing Embarked with mode'):
    data['Embarked'].fillna(data['Embarked'].mode()[0], inplace=True)

if st.checkbox('Drop duplicates'):
    data.drop_duplicates(inplace=True)

st.subheader('Cleaned Dataset')
st.dataframe(data.head())

# EDA Section
st.subheader('Statistical Summary of the Data')
st.write(data.describe())

# Age Distribution
st.subheader('Age Distribution')
fig, ax = plt.subplots()
sns.histplot(data['Age'], kde=True, ax=ax)
ax.set_title('Age Distribution')
st.pyplot(fig)

# Gender Distribution
st.subheader('Gender Distribution')
fig, ax = plt.subplots()
sns.countplot(x='Sex', data=data, ax=ax)
ax.set_title('Gender Distribution')
st.pyplot(fig)

# Pclass vs Survived
st.subheader('Pclass vs Survived')
fig, ax = plt.subplots()
sns.countplot(x='Pclass', hue='Survived', data=data, ax=ax)
ax.set_title('Pclass vs Survived')
st.pyplot(fig)

'''
# Correlation Heatmap
st.subheader('Correlation Heatmap')
fig, ax = plt.subplots()
sns.heatmap(data.corr(), annot=True, cmap='coolwarm', ax=ax)
ax.set_title('Correlation Heatmap')
st.pyplot(fig)
'''

# Feature Engineering Section
st.subheader('Feature Engineering: Family Size')
data['FamilySize'] = data['SibSp'] + data['Parch']
fig, ax = plt.subplots()
sns.histplot(data['FamilySize'], kde=True, ax=ax)
ax.set_title('Family Size Distribution')
st.pyplot(fig)

# Conclusion Section
st.subheader('Key Insights')
insights = """
- Females have a higher survival rate than males.
- Passengers in 1st class had the highest survival rate.
- The majority of passengers are in Pclass 3.
- Younger passengers tended to survive more often.
"""
st.write(insights)