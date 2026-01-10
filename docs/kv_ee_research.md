# KV.ee Research Notes

## Overview
KV.ee is Estonia's leading real estate portal (since 1999). No public API available.

## Access Constraints
- **Anti-bot protection**: Returns HTTP 403 for plain automated requests
- **Requires**: Browser-like headers (User-Agent, Accept, etc.)
- **Fallback**: May need headless browser if JS rendering is required

## URL Patterns

### Search URL Structure
```
https://www.kv.ee/?act=search.simple&<parameters>
```

Or the newer format:
```
https://www.kv.ee/en/search?<parameters>
```

### Known Query Parameters

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| `act` | Action type | `search.simple` |
| `deal_type` | Transaction type | `1` (sale), `2` (rent) |
| `county` | County/region code | `0` (all), numeric codes |
| `parish` | Municipality | string |
| `price_min` | Minimum price | integer |
| `price_max` | Maximum price | integer |
| `rooms_min` | Min rooms | integer |
| `rooms_max` | Max rooms | integer |
| `area_min` | Min area (m²) | integer |
| `area_max` | Max area (m²) | integer |
| `floor_min` | Min floor | integer |
| `floor_max` | Max floor | integer |
| `page` | Pagination | integer |
| `page_size` | Results per page | integer |
| `orderby` | Sort order | `ob` (default) |
| `keyword` | Address/keyword search | string |

### Listing URL Pattern
Individual listings appear to follow:
```
https://www.kv.ee/<listing-id>.html
```

## HTML Structure (to be confirmed)
- Search results likely in a list/grid container
- Each listing card contains: title, price, location, area, rooms, image
- Listing ID embedded in URL or data attribute

## Rate Limiting Strategy
- Minimum 2-3 second delay between requests
- Session reuse with cookies
- Realistic User-Agent rotation
- Respect any Retry-After headers

## Implementation Notes
1. Start with requests + proper headers
2. If 403 persists, try with browser automation (playwright/selenium)
3. Parse HTML with BeautifulSoup4
4. Extract listing data to structured format
