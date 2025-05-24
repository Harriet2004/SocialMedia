import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read each comments folder from the youtube folder path
path = 'datasets/youtube/'
# Creating key, values for each event
files = {
    'qatar_world_cup.csv': {'event': 'World Cup', 'year': 2022},
    'russia_world_cup.csv': {'event': 'World Cup', 'year': 2018},
    'paris_olympics.csv': {'event': 'Olympics', 'year': 2024},
    'tokyo_olympics.csv': {'event': 'Olympics', 'year': 2021} 
}

dfs = []
for file, meta in files.items():
    df = pd.read_csv(path + file)
    df['event'] = meta['event']
    df['year'] = meta['year']
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
print("Combined shape:", df.shape)
df.head()

# Unique users 
sns.set(style='whitegrid')
user_count = df.groupby(['event', 'year'])['author'].nunique().reset_index()
user_count.columns = ['Event', 'year', 'unique_users']

plt.figure(figsize=(8, 5))
sns.barplot(data=user_count, x='year', y='unique_users', hue='Event', palette='Set2')
plt.title("Number of Unique Users by Event and Year")
plt.xlabel("Year")
plt.ylabel("Unique Youtube Users")
plt.tight_layout()
plt.show()

# Activity Timeline by Event
df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
df['date'] = df['datetime'].dt.date

activity_by_date = df.groupby(['date', 'event']).size().reset_index(name='count')
plt.figure(figsize=(10, 5))
sns.lineplot(data=activity_by_date, x='date', y='count', hue='event', marker='o')
plt.title("Youtube Activity Timeline by Event")
plt.xlabel("Date")
plt.ylabel("Number of Comments")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()