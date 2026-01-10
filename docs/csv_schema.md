# CSV Schema Definition

## Output File
Default: `output/listings.csv`

## Columns (in order)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `id` | string | yes | Unique listing ID from kv.ee (deduplication key) |
| `url` | string | yes | Full URL to the listing |
| `title` | string | yes | Listing title/headline |
| `deal_type` | string | yes | "sale" or "rent" |
| `price` | integer | yes | Price in EUR (normalized, no symbols) |
| `price_per_m2` | float | no | Price per square meter |
| `area_m2` | float | no | Total area in square meters |
| `rooms` | integer | no | Number of rooms |
| `floor` | integer | no | Floor number |
| `total_floors` | integer | no | Total floors in building |
| `location` | string | yes | Full address/location |
| `county` | string | no | County/region |
| `city` | string | no | City/town |
| `district` | string | no | District/neighborhood |
| `property_type` | string | no | apartment, house, land, etc. |
| `build_year` | integer | no | Year built |
| `condition` | string | no | Property condition |
| `first_seen` | datetime | yes | ISO 8601 timestamp when first scraped |
| `last_seen` | datetime | yes | ISO 8601 timestamp of most recent scrape |
| `is_active` | boolean | yes | Whether listing is still active |

## Deduplication
- Primary key: `id`
- On update: merge new data, update `last_seen`, preserve `first_seen`

## Data Normalization
- Prices: Remove spaces, "€" symbol, convert to integer
- Areas: Remove "m²", convert to float
- Dates: ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- Booleans: lowercase "true"/"false"

## Example Row
```csv
id,url,title,deal_type,price,price_per_m2,area_m2,rooms,floor,total_floors,location,county,city,district,property_type,build_year,condition,first_seen,last_seen,is_active
12345,https://www.kv.ee/12345.html,3-room apartment in Mustamäe,sale,150000,2500.0,60.0,3,5,9,"Mustamäe tee 183, Tallinn",Harju,Tallinn,Mustamäe,apartment,1985,renovated,2024-01-15T10:30:00,2024-01-20T14:00:00,true
```
