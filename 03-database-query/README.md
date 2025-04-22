# Database Query Example

This example demonstrates how to use MCP to query a SQLite database. We use the Chinook database, which represents a digital media store with tables for artists, albums, tracks, customers, and more.

## Setup

```bash
# Install dependencies
uv pip install -e .

# Run the server
python server.py
```

## How to Use with LLMs

You can interact with this MCP server through natural language. Here are examples of questions you can ask the LLM:

### Data Exploration
- "What tables are available in the database?"
- "Can you show me the structure of the Customer table?"
- "Give me a summary of what kind of data is stored in this database"

### Business Analysis Questions
1. Customer Insights:
   - "Who are our most valuable customers and how much have they spent?"
   - "What's the average purchase amount per customer?"
   - "Show me which countries generate the most revenue"
   - "Can you identify any patterns in customer purchasing behavior?"

2. Music Catalog Analysis:
   - "What are the most popular music genres in our store?"
   - "Find all albums by Queen and sort them by popularity"
   - "Which artists have the most tracks in our database?"
   - "What's the average length of songs by genre?"

3. Sales Performance:
   - "Compare sales performance across different regions"
   - "What was the total revenue last year?"
   - "Show me the top-selling tracks of all time"
   - "Which genres generate the most revenue?"

4. Complex Analysis:
   - "Can you analyze the relationship between track length and popularity?"
   - "Find any interesting correlations between genre and customer purchases"
   - "What's the distribution of track prices across different genres?"
   - "Identify any seasonal patterns in our sales data"

### Data Export and Visualization Requests
- "Can you export the top 100 selling tracks to a CSV format?"
- "Create a summary report of our sales by country"
- "Generate a list of all artists and their total revenue"
- "Show me a breakdown of sales by genre in a table format"

### Database Maintenance
- "Check if there are any tracks without an associated album"
- "Find any duplicate customer records"
- "Verify the integrity of our invoice data"
- "List any missing or incomplete data in the customer records"

## Tips for Better Results
1. Be Specific:
   - Instead of: "Show me sales data"
   - Better: "Show me total sales by country for the last year"

2. Use Context:
   - Instead of: "Find Queen"
   - Better: "Find all albums and tracks by Queen"

3. Ask for Analysis:
   - Instead of: "Show customer data"
   - Better: "Analyze customer spending patterns and identify top spenders"

4. Request Formats:
   - "Can you format this as a table?"
   - "Could you show this data in a more readable way?"
   - "Please sort this by revenue in descending order"

## Example Workflows

### Customer Analysis Workflow
1. "Show me a list of all customers"
2. "Who are our top 5 spending customers?"
3. "What genres do our top customers prefer?"
4. "Generate a report of customer spending patterns"

### Music Catalog Analysis Workflow
1. "List all available genres"
2. "Show me the most popular artists in each genre"
3. "Which albums have the most tracks?"
4. "Compare average track lengths across different genres"

### Sales Analysis Workflow
1. "Show total sales by country"
2. "Which genres generate the most revenue?"
3. "Identify our peak sales periods"
4. "Generate a summary of our best-performing products"

## Technical Details

## Database Schema

The Chinook database includes the following main tables:
- `Artist`: Music artists
- `Album`: Music albums
- `Track`: Individual songs
- `Customer`: Store customers
- `Invoice`: Customer purchases
- `Genre`: Music genres
- `Playlist`: User playlists

## Sample Questions

You can ask natural language questions about the data. Here are some examples:

1. Basic Queries:
   - "Show me all albums by Queen"
   - "List the top 10 longest tracks"
   - "What genres are available in the store?"
   - "How many tracks are in each genre?"

2. Sales Analysis:
   - "Who are our top 5 customers by purchase amount?"
   - "What are the best-selling genres?"
   - "Show total sales by country"
   - "Which artist generated the most revenue?"

3. Complex Queries:
   - "What is the average length of tracks by genre?"
   - "Show me customers who bought jazz tracks"
   - "List albums that have more than 10 tracks"
   - "Find artists who have tracks in multiple genres"

4. Playlist Analysis:
   - "What are the most common genres in playlists?"
   - "Show me the longest and shortest playlists"
   - "Which tracks appear in the most playlists?"
   - "List playlists that contain classical music"

## API Usage

### HTTP Endpoints

```bash
# List all tables
GET /tables

# Get table schema
GET /schema/{table_name}

# Execute custom query
POST /query
{
    "query": "SELECT * FROM Artist WHERE Name LIKE '%Queen%'"
}
```

### MCP Tools

1. `list_tables`: List all available tables
   ```python
   result = await client.call_tool("list_tables")
   ```

2. `get_schema`: Get schema for a specific table
   ```python
   result = await client.call_tool("get_schema", {"table": "Artist"})
   ```

3. `query`: Execute a SQL query
   ```python
   result = await client.call_tool("query", {
       "query": "SELECT * FROM Artist LIMIT 5"
   })
   ```

4. `ask`: Ask natural language questions about the data
   ```python
   result = await client.call_tool("ask", {
       "question": "Show me all albums by Queen"
   })
   ```

## Example Queries

Here are some example SQL queries you can try:

```sql
-- Find top selling artists
SELECT 
    ar.Name as Artist,
    COUNT(il.TrackId) as TracksSold,
    SUM(il.UnitPrice) as TotalRevenue
FROM Artist ar
JOIN Album al ON ar.ArtistId = al.ArtistId
JOIN Track t ON al.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY ar.ArtistId, ar.Name
ORDER BY TracksSold DESC
LIMIT 10;

-- Find most popular genres
SELECT 
    g.Name as Genre,
    COUNT(t.TrackId) as TrackCount,
    COUNT(DISTINCT al.ArtistId) as ArtistCount
FROM Genre g
JOIN Track t ON g.GenreId = t.GenreId
JOIN Album al ON t.AlbumId = al.AlbumId
GROUP BY g.GenreId, g.Name
ORDER BY TrackCount DESC;

-- Customer spending by country
SELECT 
    BillingCountry,
    COUNT(DISTINCT CustomerId) as CustomerCount,
    SUM(Total) as TotalSpent
FROM Invoice
GROUP BY BillingCountry
ORDER BY TotalSpent DESC;
``` 