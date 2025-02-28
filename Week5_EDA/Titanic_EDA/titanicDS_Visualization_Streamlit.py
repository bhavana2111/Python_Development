import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


dataSet = pd.read_csv(r'C:\Users\bmittipa\Documents\Vodafone\PrakashSenapati\Python_Learning\Week5_EDA\Titanic_EDA\titanic_dataset.csv')
st.set_page_config(layout="wide")

st.title("Exploratory DataAnalysis for Titanic Dataset")
st.write("This page covers Data analysis captured for Titanic Dataset.")
st.write("Glimpse of the dataset to understand features/attributes.")
st.write(dataSet)

st.subheader("Let us start by checking for Null/Empty values in the Dataset.")
st.write(dataSet.isnull().sum())

st.subheader("Let us fix the Null values and Empty values.")
fill_method_age = st.radio('Choose the way to full empty values of Age Attribute',
                            ('Fill Missing age using Average of other ages',
                             'Fill Missing age using Median/Middle of other ages',
                             'Fill Missing age using the most common of all ages'),
                             key = 'age_fill')
if fill_method_age == 'Fill Missing age using Average of other ages':
    dataSet['Age'].fillna(np.round(pd.to_numeric(dataSet['Age'].mean())),inplace=True)
if fill_method_age == 'Fill Missing age using Median/Middle of other ages':
    dataSet['Age'].fillna(np.round(pd.to_numeric(dataSet['Age'].median())),inplace=True)
if fill_method_age == 'Fill Missing age using the most common of all ages':
    dataSet['Age'].fillna(pd.to_numeric(dataSet['Age'].mode()[0]),inplace=True)

fill_method_cabin = st.radio('Choose the way to fill empty CABIN information',
         ('Fill Cabin information with the most common value of the Cabin Feature set',
          'Fill Cabin information with default value Unknown Cabin'),
           key = 'cabin_fill')
if fill_method_cabin == 'Fill Cabin information with the most common value of the Cabin Feature set':
    dataSet['Cabin'].fillna(np.random.choice(dataSet['Cabin'].mode()),inplace=True)
if fill_method_cabin == 'Fill Cabin information with default value Unknown Cabin':
    dataSet['Cabin'].fillna('Unknown Cabin',inplace=True)

fill_method_embarked = st.radio('Choose the way to fill empty embarked information',
         ('Fill embarked information with the most common value of the embarked Feature set',
          'Fill embarked information with the next row value',
          'Fill embarked information with the previous row value'),
           key = 'embark_fill')
if fill_method_embarked == 'Fill embarked information with the most common value of the Embarked Feature set':
    dataSet['Embarked'].fillna(dataSet['Embarked'].mode()[0],inplace=True)
if fill_method_embarked == 'Fill embarked information with the next row value':
    dataSet['Embarked'].fillna(method='bfill',axis=0,inplace=True)
if fill_method_embarked == 'Fill embarked information with the previous row value':
    dataSet['Embarked'].fillna(method='ffill',axis=0,inplace=True)

st.subheader("Clean Data Set")
st.write(dataSet.head(10))

st.subheader("Listing Statistical summary for the Data set")
st.write(dataSet.describe())


# AGE Distribution
st.subheader("Age Distribution")
fig,ax = plt.subplots()
ax.set_title('Histogram for Age Distribution')
age_distibution_options = st.radio('Choose KDE Curve for Age Distibution Histogram?',
                                    ('Yes', 'No'))
if age_distibution_options == 'Yes':
    sns.histplot(dataSet['Age'],kde=True,ax=ax)
elif age_distibution_options == 'No':
    sns.histplot(dataSet['Age'],kde=False,ax=ax)
st.pyplot(fig)


# GENDER DISTRIBUTION
st.subheader("Gender Distribution")
fig,ax = plt.subplots()
sns.countplot(x=dataSet['Sex'],data = dataSet,ax=ax)
ax.set_title('Count Plot for Gender')
st.pyplot(fig)

# Passenger class Survived
st.subheader("Passenger Class Survived.")
fig,ax = plt.subplots()
sns.countplot(x=dataSet['Pclass'],data = dataSet,hue ='Survived', ax=ax)
ax.set_title('Passenger class survived')
st.pyplot(fig)

# Family Distribution
st.subheader("Family Distribution")
fig,ax = plt.subplots()
ax.set_title("Family Distribution Histogram.")
dataSet['Family'] = dataSet['SibSp']+dataSet['Parch']
sns.histplot(dataSet['Family'],kde=True,ax=ax)
st.pyplot(fig)

st.subheader('Insights collected from the Above Visualizations are :- ')
insights = """
- Age distribution is mostly around ages 30-35 years
- Male Passengers onboarded are more than Females
- Class 3 Survival is more
- Family members are mostly 2 or less in a given family.
"""
st.write(insights)