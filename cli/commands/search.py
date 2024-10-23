"""Tournament search command implementation."""

from datetime import datetime
from typing import Optional
import typer
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

from .. import app, console
from ..formatters.tournament import create_tournament_table
from .results import results as results_command
from pysmashgg.api import run_query
from pysmashgg import filters

# Import the global SmashGG instance
import startgg

# Custom GraphQL query to get tournament owner information
TOURNAMENT_OWNER_QUERY = """query ($tourneySlug: String!) {
  tournament(slug: $tourneySlug) {
    id
    name
    owner {
      id
      player {
        gamerTag
      }
    }
  }
}"""

def get_tournament_owner(tournament_slug: str):
    """Get the owner ID and information for a tournament
    
    Args:
        tournament_slug: The tournament slug to look up
        
    Returns:
        Dictionary containing:
        - id: Owner's ID
        - name: Owner's gamer tag
        - tournament_name: Name of the tournament
        Returns None if owner information cannot be found
    """
    try:
        variables = {"tourneySlug": tournament_slug}
        response = run_query(TOURNAMENT_OWNER_QUERY, variables, startgg.smash.header, startgg.smash.auto_retry)
        if response and 'data' in response and 'tournament' in response['data']:
            tournament = response['data']['tournament']
            if 'owner' in tournament and tournament['owner']:
                return {
                    'id': tournament['owner']['id'],
                    'name': tournament['owner']['player']['gamerTag'] if tournament['owner']['player'] else 'Unknown',
                    'tournament_name': tournament['name']
                }
    except Exception as e:
        console.print(f"[red]Error getting tournament owner:[/] {str(e)}")
    return None

@app.command()
def search(
    owner_id: Optional[int] = typer.Option(None, "--owner", "-o", help="Search by tournament organizer's ID"),
    tournament_slug: Optional[str] = typer.Option(None, "--tournament", "-t", 
                                                help="Get owner ID from a tournament slug and search their tournaments"),
    page: int = typer.Option(1, "--page", "-p", help="Page number for results"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of tournaments to display"),
    select: bool = typer.Option(False, "--select", "-s", help="Interactively select a tournament to view results")
):
    """Search for tournaments by owner ID or tournament slug.
    
    This command allows searching for tournaments in two ways:
    1. Directly by owner ID using the --owner option
    2. By tournament slug using the --tournament option, which first looks up the owner
    
    The results can be paginated using --page and limited using --limit.
    Using --select enables interactive tournament selection to view results.
    """
    try:
        # If tournament slug is provided, get the owner ID
        if tournament_slug and not owner_id:
            with console.status(f"[bold green]Getting owner information for tournament {tournament_slug}..."):
                owner_info = get_tournament_owner(tournament_slug)
                if owner_info:
                    owner_id = owner_info['id']
                    console.print(f"\nFound tournament organizer: [cyan]{owner_info['name']}[/] (ID: {owner_id})")
                    console.print(f"From tournament: [cyan]{owner_info['tournament_name']}[/]")
                else:
                    console.print("[red]Could not find tournament owner information[/]")
                    return

        if not owner_id:
            console.print("[red]Please provide either an owner ID or a tournament slug[/]")
            return

        with console.status("[bold green]Searching for tournaments..."):
            # Get tournaments using the SmashGG instance
            tournaments = startgg.smash.tournament_show_by_owner(owner_id, page)
            
            # Debug: Print the first tournament to see its structure
            if tournaments and len(tournaments) > 0:
                console.print("\n[yellow]Debug: First tournament structure:[/]")
                console.print(tournaments[0])
                
            if not tournaments:
                console.print("[yellow]No tournaments found for this owner ID[/]")
                return

            # Process tournaments for display
            displayed_tournaments = tournaments[:limit]
            table = create_tournament_table(displayed_tournaments, owner_id)
            console.print(table)
            
            if len(tournaments) > limit:
                console.print(f"\n[yellow]Showing {limit} of {len(tournaments)} tournaments. Use --limit to see more.[/]")

            if select:
                # Allow user to select a tournament and view its results
                choice = Prompt.ask(
                    "\nEnter tournament number to view results",
                    choices=[str(i) for i in range(1, len(displayed_tournaments) + 1)],
                    show_choices=False
                )
                
                selected_tournament = displayed_tournaments[int(choice) - 1]
                console.print(f"\n[green]Selected tournament:[/] {selected_tournament['name']}")
                
                # Call the results command for the selected tournament
                results_command(selected_tournament['slug'])
            else:
                # Add tips about using the tournament slug
                console.print("\n[cyan]Tips:[/]")
                console.print("1. Use the tournament slug with the 'results' command to view tournament results:")
                console.print("[green]   python startgg.py results <tournament-slug>[/]")
                console.print("2. Use --select (-s) flag to interactively select a tournament:")
                console.print("[green]   python startgg.py search --owner <id> --select[/]")
                console.print("3. Search using a tournament slug to find more tournaments by the same organizer:")
                console.print("[green]   python startgg.py search --tournament <tournament-slug>[/]")

    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(code=1)
