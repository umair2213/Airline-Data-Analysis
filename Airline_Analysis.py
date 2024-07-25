import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# DATABASE CONNECTION
# Connect to the SQLite database 'travel.sqlite' and create a cursor object
connection = sqlite3.connect('travel.sqlite')
cursor = connection.cursor()

# List tables in the database
cursor.execute("""select name from sqlite_master where type = 'table';""")
print('List of tables present in database:')
table_List = [table[0] for table in cursor.fetchall()]
print(table_List)

# Function to load table data and display first few rows
def load_table(table_name):
    df = pd.read_sql_query(f"select * from {table_name}", connection)
    print(f"\nLoaded {table_name}:")
    print(df.head())
    return df

# DATA EXPLORATION
# Load data from each table and print the first few rows
aircrafts_data = load_table('aircrafts_data')
airports_data = load_table('airports_data')
boarding_passes = load_table('boarding_passes')
bookings = load_table('bookings')
flights = load_table('flights')
seats = load_table('seats')
ticket_flights = load_table('ticket_flights')
tickets = load_table('tickets')

# Print column information for each table
for table in table_List:
    print('\nTable:', table)
    column_info = connection.execute(f"PRAGMA table_info({table})")
    for column in column_info.fetchall():
        print(column[1:3])

# Check for null values in each table
for table in table_List:
    print("\nTable:", table)
    df_table = pd.read_sql_query(f"select * from {table}", connection)
    print(df_table.isnull().sum())        

# BASIC ANALYSIS

# Question 1: Planes have more than 100 seats
# Retrieve the number of seats for each aircraft code
planes_more_than_100_seats = pd.read_sql_query("""select aircraft_code, count(*) as num_seats from seats 
                                                  group by aircraft_code""", connection)
print("\nPlanes with more than 100 seats:")
print(planes_more_than_100_seats)

# Question 2: Number of tickets booked and total amount changed with time
# Merge tickets and bookings data, extract booking dates, and count tickets per date
tickets = pd.read_sql_query("""select * from tickets inner join bookings
                               on tickets.book_ref = bookings.book_ref""", connection)
tickets['book_date'] = pd.to_datetime(tickets['book_date'])
tickets['date'] = tickets['book_date'].dt.date

tickets_count_by_date = tickets.groupby('date')[['date']].count()
print("\nTickets count by date:")
print(tickets_count_by_date.head())

# Plot the count of tickets by date
tickets_count_by_date.plot(kind='line')
plt.xlabel('Date')
plt.ylabel('Count of Tickets')
plt.title('Count of Tickets by Date')
plt.show()

# Extract booking dates and sum total amounts per date
bookings = pd.read_sql_query("""select * from bookings""", connection)
bookings['book_date'] = pd.to_datetime(bookings['book_date'])
bookings['date'] = bookings['book_date'].dt.date

total_amount_by_date = bookings.groupby('date')[['total_amount']].sum()
print("\nTotal amount earned by date:")
print(total_amount_by_date.head())

# Plot the total amount earned by date
total_amount_by_date.plot(kind='line')
plt.xlabel('Date')
plt.ylabel('Total Amount Earned')
plt.title('Total Amount Earned by Date')
plt.show()

# Question 3: Calculate average charges for each aircraft with different fare conditions
# Retrieve average ticket amount for each aircraft code and fare condition
avg_charges_by_aircraft = pd.read_sql_query("""select aircraft_code, avg(amount) as avg_amount, fare_conditions 
                                               from ticket_flights join flights
                                               on ticket_flights.flight_id = flights.flight_id
                                               group by aircraft_code, fare_conditions""", connection)
print("\nAverage charges by aircraft and fare conditions:")
print(avg_charges_by_aircraft)

# Plot average charges by aircraft code and fare conditions
sns.barplot(data=avg_charges_by_aircraft, x='aircraft_code', y='avg_amount', hue='fare_conditions')
plt.show()

# ANALYZING OCCUPANCY RATE

# Question 1: For each aircraft, calculate the total revenue per year and the avg revenue per ticket
# Retrieve total revenue and average revenue per ticket for each aircraft code
revenue_per_ticket = pd.read_sql_query("""select aircraft_code, ticket_count, total_revenue, 
                                          total_revenue/ticket_count as avg_revenue_per_ticket from
                                          (select aircraft_code, count(*) as ticket_count, sum(amount) as total_revenue 
                                           from ticket_flights join flights on ticket_flights.flight_id = flights.flight_id 
                                           group by aircraft_code)""", connection)
print("\nTotal revenue and average revenue per ticket:")
print(revenue_per_ticket)

# Question 2: Calculate avg occupancy per aircraft
# Retrieve average occupancy rate for each aircraft code
occupancy_rate = pd.read_sql_query(""" SELECT a.aircraft_code, 
                                       AVG(a.seat_count) AS booked_seats, 
                                       b.num_seats, 
                                       AVG(a.seat_count) / b.num_seats AS occupancy_rate
                                       FROM (SELECT aircraft_code, flights.flight_id, COUNT(*) AS seat_count 
                                             FROM boarding_passes
                                             INNER JOIN flights ON boarding_passes.flight_id = flights.flight_id 
                                             GROUP BY aircraft_code, flights.flight_id) AS a
                                       INNER JOIN (SELECT aircraft_code, COUNT(*) AS num_seats 
                                                   FROM seats 
                                                   GROUP BY aircraft_code) AS b
                                       ON a.aircraft_code = b.aircraft_code 
                                       GROUP BY a.aircraft_code
                                       """, connection)
print("\nOccupancy rate per aircraft:")
print(occupancy_rate)

# Question 3: Calculate by how much total annual turnover could increase by giving all aircraft 10% higher occupancy rate
# Calculate increased occupancy rate and total annual turnover with 10% higher occupancy rate
occupancy_rate['Inc occupancy rate'] = occupancy_rate['occupancy_rate'] + occupancy_rate['occupancy_rate'] * 0.1
print("\nOccupancy rate with 10% increase:")
print(occupancy_rate)

# Retrieve total revenue for each aircraft code
total_revenue = pd.read_sql_query("""select aircraft_code, sum(amount) as total_revenue 
                                     from ticket_flights join flights on ticket_flights.flight_id = flights.flight_id 
                                     group by aircraft_code""", connection)

# Calculate increased total annual turnover
occupancy_rate['Inc Total Annual Turnover'] = (total_revenue['total_revenue'] / occupancy_rate['occupancy_rate']) * occupancy_rate['Inc occupancy rate']
print("\nIncreased total annual turnover with 10% higher occupancy rate:")
print(occupancy_rate)
