import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import aiohttp
import datetime
from db.db import DatabaseUser
from datetime import datetime, timedelta
import sys
import os

# Load environment variables from .env file
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Get the bot token from the environment
TOKEN = os.getenv('DISCORD_TOKEN')
api_key = 'dc50955858f57f'
channel_id = 1274580261807456381
# Enable all intents
intents = discord.Intents.all()
db = DatabaseUser()

# Create a bot instance with all intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Sync app commands upon bot startup
@bot.event
async def on_ready():
    # Sync the app commands across all guilds
    try:
        await bot.tree.sync()  # Sync slash commands
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")
        print("App commands synced successfully.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Register an app command (slash command)
@bot.tree.command(name="hello", description="Says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

@bot.tree.command(name="whois", description="Get nation information from Politics and War.")
@app_commands.describe(nation="Provide a nation ID or nation name to fetch their nation information.")
async def whois(interaction: discord.Interaction, nation: str):
    if nation.isdigit():
        nation_id = int(nation)
    else:
        async with aiohttp.ClientSession() as session:
        # Properly include the nation_id in the query string
            query = f"""
            {{
                nations(first:1 nation_name:"{nation}") {{
                    data {{
                        id
                    }}
                }}
            }}
            """
            api_url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"

            async with session.post(api_url, json={'query': query}) as response:
                res = await response.json()
                try:
                    nation = res['data']['nations']['data'][0]
                    nation_id = nation['id']
                except (KeyError, IndexError):
                    # Send the full response as a message for debugging
                    await interaction.response.send_message(f"No nation found with ID `{nation}`")
    async with aiohttp.ClientSession() as session:
        # Properly include the nation_id in the query string
        query = f"""
    {{
        nations(first: 1 id: {nation_id}) {{
            data {{
                id
                nation_name
                discord
                leader_name
                num_cities
                cia
                spy_satellite
                warpolicy
                population
                dompolicy
                flag
                vmode
                color
                beigeturns
                last_active
                soldiers
                tanks
                aircraft
                ships
                nukes
                missiles
                mlp
                nrf
                vds
                irond
                wars {{
                    attid
                    turnsleft
                }}
                cities {{
                    barracks
                    factory
                    airforcebase
                    drydock
                }}
                score
                alliance_position
                alliance_seniority
                alliance {{
                    name
                    id
                    score
                    color
                }}
            }}
        }}
    }}
    """
    
    async with aiohttp.ClientSession() as session:
        api_url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"
        async with session.post(api_url, json={'query': query}) as response:
            result = await response.json()
            
            try:
                # Extracting nation data
                nation = result['data']['nations']['data'][0]
                last_active = datetime.fromisoformat(nation['last_active'].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")             
                # Create the first embed for core nation info
                embed = discord.Embed(title=f"Nation Details for {nation['nation_name']}", color=discord.Color.blue())
                embed.add_field(name="ID", value=nation['id'], inline=True)
                embed.add_field(name="Nation Name", value=nation['nation_name'], inline=True)
                embed.add_field(name="Leader", value=nation['leader_name'], inline=True)
                embed.add_field(name="Discord", value=nation['discord'], inline=True)
                embed.add_field(name="Cities", value=nation['num_cities'], inline=True)
                embed.add_field(name="War Policy", value=nation['warpolicy'], inline=True)
                embed.add_field(name="Domestic Policy", value=nation['dompolicy'], inline=True)
                embed.add_field(name="Vacation Mode", value=nation['vmode'], inline=True)
                embed.add_field(name="Color", value=nation['color'], inline=True)
                embed.add_field(name="Last Active", value=last_active, inline=True)
                
                # Military information (split across two embeds)
                embed2 = discord.Embed(title=f"Military and Wars for {nation['nation_name']}", color=discord.Color.green())
                embed2.add_field(name="Soldiers", value=nation['soldiers'], inline=True)
                embed2.add_field(name="Tanks", value=nation['tanks'], inline=True)
                embed2.add_field(name="Aircraft", value=nation['aircraft'], inline=True)
                embed2.add_field(name="Ships", value=nation['ships'], inline=True)
                embed2.add_field(name="Nukes", value=nation['nukes'], inline=True)
                embed2.add_field(name="Missiles", value=nation['missiles'], inline=True)

                # Wars (ensure we don’t exceed field limits)
                wars = nation['wars']
                if wars:
                    for war in wars[:5]:  # Limit to 5 wars to stay under 25 fields in total
                        embed2.add_field(name=f"War Attacker ID: {war['attid']}", value=f"Turns Left: {war['turnsleft']}", inline=False)
                
                # Alliance information
                alliance = nation['alliance']
                if alliance:
                    embed3 = discord.Embed(title=f"Alliance", color=discord.Color.orange())
                    alliance_score= alliance['score']
                    embed3.add_field(name="Alliance Name", value=alliance['name'], inline=True)
                    embed3.add_field(name="Alliance ID", value=alliance['id'], inline=True)
                    embed3.add_field(name="Alliance Score", value=f'{alliance_score:,}', inline=True)
                    embed3.add_field(name="Alliance Color", value=alliance['color'], inline=True)
                
                # Sending the embedded messages with nation details
                await interaction.response.send_message(embeds=[embed, embed2, embed3])
            except (KeyError, IndexError):
                await interaction.response.send_message(f"Could not find details for nation with ID {nation}")
@tasks.loop(seconds=5)
async def trade_price():
    async with aiohttp.ClientSession() as session:
        query = """
        {
            tradeprices(first: 1) {
                data {
                    food
                    coal
                    oil
                    uranium
                    iron
                    bauxite
                    lead
                    gasoline
                    munitions
                    steel
                    aluminum
                }
            }
        }
        """
        
        api_url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"
        async with session.post(api_url, json={'query': query}) as response:
            result = await response.json()

            # Extract current trade prices from the response
            current_prices = result['data']['tradeprices']['data'][0]
            food_current = current_prices['food']
            coal_current = current_prices['coal']
            oil_current = current_prices['oil']
            uranium_current = current_prices['uranium']
            iron_current = current_prices['iron']
            bauxite_current = current_prices['bauxite']
            lead_current = current_prices['lead']
            gasoline_current = current_prices['gasoline']
            munitions_current = current_prices['munitions']
            steel_current = current_prices['steel']
            aluminum_current = current_prices['aluminum']

            # Retrieve earlier prices
            earlier_prices = await db.get_latest_trade_prices()
            if earlier_prices:
                # Calculate the difference between current and earlier prices
                food_difference = food_current - earlier_prices[1]
                coal_difference = coal_current - earlier_prices[2]
                oil_difference = oil_current - earlier_prices[3]
                uranium_difference = uranium_current - earlier_prices[4]
                iron_difference = iron_current - earlier_prices[5]
                bauxite_difference = bauxite_current - earlier_prices[6]
                lead_difference = lead_current - earlier_prices[7]
                gasoline_difference = gasoline_current - earlier_prices[8]
                munitions_difference = munitions_current - earlier_prices[9]
                steel_difference = steel_current - earlier_prices[10]
                aluminum_difference = aluminum_current - earlier_prices[11]

                # Prepare the message with the differences
                differences_message = (
                    f"Trade Price Differences:\n"
                    f"Food: {food_difference}\n"
                    f"Coal: {coal_difference}\n"
                    f"Oil: {oil_difference}\n"
                    f"Uranium: {uranium_difference}\n"
                    f"Iron: {iron_difference}\n"
                    f"Bauxite: {bauxite_difference}\n"
                    f"Lead: {lead_difference}\n"
                    f"Gasoline: {gasoline_difference}\n"
                    f"Munitions: {munitions_difference}\n"
                    f"Steel: {steel_difference}\n"
                    f"Aluminum: {aluminum_difference}"
                )
                
                # Send the message to your desired channel
                channel = bot.get_channel(channel_id)
                await channel.send(differences_message)

            # Store the current prices in the database
            await db.add_trade_price(food_current, coal_current, oil_current, uranium_current, iron_current, bauxite_current, lead_current, gasoline_current, munitions_current, steel_current, aluminum_current)
bot.run(TOKEN)
