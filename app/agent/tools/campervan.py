from app.db import get_connection


async def search_campervans(destination: str = None, travelers: int = None, budget: int = None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT id, name, location, capacity, price_per_day
        FROM campervans
        WHERE 1=1
    """

    params = []

    if destination:
        query += " AND location ILIKE %s"
        params.append(f"%{destination}%")

    if travelers:
        query += " AND capacity >= %s"
        params.append(travelers)

    if budget:
        query += " AND price_per_day <= %s"
        params.append(budget)

    cur.execute(query, params)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    campervans = []

    for row in rows:
        campervans.append({
            "id": row[0],
            "name": row[1],
            "location": row[2],
            "capacity": row[3],
            "price_per_day": row[4]
        })

    return campervans


search_campervans_declaration = {
    "name": "search_campervans",
    "description": "Search available campervans based on destination, travelers, and budget",
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "Destination or location where user wants a campervan"
            },
            "travelers": {
                "type": "integer",
                "description": "Number of travelers"
            },
            "budget": {
                "type": "integer",
                "description": "Maximum price per day"
            }
        }
    }
}

