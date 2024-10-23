"""Tournament table formatting utilities."""

from datetime import datetime
from rich.table import Table

def create_tournament_table(tournaments, owner_id):
    """Create a Rich table for displaying tournaments.
    
    Args:
        tournaments: List of tournament dictionaries containing tournament information
                    Each tournament should have: name, startTimestamp, city, state, entrants, slug
        owner_id: ID of the tournament organizer
    
    Returns:
        Rich Table object containing formatted tournament information with columns:
        - #: Index number
        - Name: Tournament name
        - Date: Tournament start date
        - Location: City, State
        - Entrants: Number of participants
        - Slug: Tournament slug for API reference
    """
    table = Table(title=f"Tournaments by Owner ID: {owner_id}")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Location", style="blue")
    table.add_column("Entrants", justify="right", style="magenta")
    table.add_column("Slug", style="white", overflow="fold")

    for idx, tournament in enumerate(tournaments, 1):
        # Convert timestamp to readable date
        start_date = datetime.fromtimestamp(tournament.get('startTimestamp', 0)).strftime('%Y-%m-%d')
        # Format location as "City, State"
        location = f"{tournament.get('city', 'N/A')}, {tournament.get('state', 'N/A')}"
        # Get entrants count, defaulting to N/A if not available
        entrants = str(tournament.get('entrants', 'N/A'))
        
        table.add_row(
            str(idx),
            tournament['name'],
            start_date,
            location,
            entrants,
            tournament['slug']
        )

    return table
