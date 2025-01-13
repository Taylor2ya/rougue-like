import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import json
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import signal
import logging

# Load environment variables from .env file
load_dotenv()

# Get the token and channel IDs from the environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GAME_CHAT_ID = int(os.getenv('GAME_CHAT_ID'))
GAME_CHANNEL_ID = int(os.getenv('GAME_CHANNEL_ID'))
ANNOUNCEMENTS_ID = int(os.getenv('ANNOUNCEMENTS_ID'))

# Initialize the bot with the required intents and make commands case-insensitive
intents = discord.Intents.default()
intents.message_content = True  # Enable the Message Content Intent
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents, case_insensitive=True)

# In-memory game state
game_state = {}

# Path to save the game state
SAVE_FILE = "game_state.json"

# Load game state when the bot starts
def load_game_state():
    global game_started
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as file:
            data = json.load(file)
            game_started = data.get("game_started", False)
            return data.get("game_state", {})
    return {}


def save_game_state():
    global game_state, game_started
    with open(SAVE_FILE, 'w') as file:
        json.dump({
            "game_state": game_state,
            "game_started": game_started
        }, file, indent=4)

game_state = load_game_state()

# Shop items
shop_items = {
    1: {"name": "RickRolling Stew", "description": "Smells like a new task!", "cost": 10, "weight": 10},
    2: {"name": "DoubleDipping Brew", "description": "Earn double points on a task if completed within 4 hours.", "cost": 15, "weight": 30},
    3: {"name": "Monkey's Paw", "description": "Re-roll a specific task with a higher chance of a harder task.", "cost": 5, "weight": 70},
    4: {"name": "GP", "description": "Award 1 million GP to each team member.", "cost": 20, "weight": 50},
    5: {"name": "Null", "description": "How'd you get this?", "cost": 50, "weight": 10},
}

def get_random_shop_items(n=2):
    items = list(shop_items.keys())
    weights = [shop_items[item]['weight'] for item in items]
    selected_items = random.choices(items, weights=weights, k=n)
    return {item_id: shop_items[item_id] for item_id in selected_items}

# Task definitions
easy_task_set = [
    {
        "id": 1,
        "tasks": [
            {"description": "Obtain any barrows item", "points": 1},
            {"description": "Obtain any 4 barrows items", "points": 2},
            {"description": "Obtain any barrows set from scratch", "points": 3}
        ]
    },
    {
        "id": 2,
        "tasks": [
            {"description": "Obtain any perlis moons item", "points": 1},
            {"description": "Obtain any 4 perlis moons items", "points": 2},
            {"description": "Obtain any perlis moons set from scratch", "points": 3}
        ]
    },
    {
        "id": 3,
        "tasks": [
            {"description": "Obtain a drop unique to wintertodt", "points": 1},
            {"description": "Obtain 3 drops unique to wintertodt", "points": 2},
            {"description": "Obtain 5 drops unique to wintertodt", "points": 3}
        ]
    },
    {
        "id": 4,
        "tasks": [
            {"description": "Obtain a drop unique to tempeross", "points": 1},
            {"description": "Obtain 3 drops unique to tempeross", "points": 2},
            {"description": "Obtain 5 drops unique to tempeross", "points": 3}
        ]
    },
    {
        "id": 5,
        "tasks": [
            {"description": "Obtain a drop unique to Guardians of the Rift", "points": 1},
            {"description": "Obtain 3 drops unique to Guardians of the Rift", "points": 2},
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 3}
        ]
    },
    {
        "id": 6,
        "tasks": [
            {"description": "Obtain 5 beginner clue uniques", "points": 1},
            {"description": "Obtain 10 beginner clue uniques", "points": 2},
            {"description": "Obtain 15 beginner clue uniques", "points": 3}
        ]
    },
    {
        "id": 7,
        "tasks": [
            {"description": "Obtain 5 easy clue uniques", "points": 1},
            {"description": "Obtain 10 easy clue uniques", "points": 2},
            {"description": "Obtain 15 easy clue uniques", "points": 3}
        ]
    },
    {
        "id": 8,
        "tasks": [
            {"description": "Obtain 5 medium clue uniques", "points": 1},
            {"description": "Obtain 10 medium clue uniques", "points": 2},
            {"description": "Obtain 15 medium clue uniques", "points": 3}
        ]
    },
    {
        "id": 9,
        "tasks": [
            {"description": "Obtain 3 hard clue uniques", "points": 1},
            {"description": "Obtain 5 hard clue uniques", "points": 2},
            {"description": "Obtain 10 hard clue uniques", "points": 3}
        ]
    },
    {
        "id": 10,
        "tasks": [
            {"description": "Obtain a granite maul", "points": 1},
            {"description": "Obtain an abyssal whip", "points": 2},
            {"description": "Obtain a drop unique to a slayer boss", "points": 3}
        ]
    },
]

medium_task_set = [
    {
        "id": 1,
        "tasks": [
            {"description": "Defeat Obor 5 times", "points": 4},
            {"description": "Defeat Obor 10 times", "points": 5},
            {"description": "Defeat Obor 15 times", "points": 6}
        ]
    },
    {
        "id": 2,
        "tasks": [
            {"description": "Defeat Bryophyta 5 times", "points": 4},
            {"description": "Defeat Bryophyta 10 times", "points": 5},
            {"description": "Defeat Bryophyta 15 times", "points": 6}
        ]
    },
    {
        "id": 3,
        "tasks": [
            {"description": "Obtain 5 drops unique to wintertodt", "points": 4},
            {"description": "Obtain 5 drops unique to wintertodt", "points": 5},
            {"description": "Obtain 5 drops unique to wintertodt", "points": 6}
        ]
    },
    {
        "id": 4,
        "tasks": [
            {"description": "Obtain 5 drops unique to tempeross", "points": 4},
            {"description": "Obtain 5 drops unique to tempeross", "points": 5},
            {"description": "Obtain 5 drops unique to tempeross", "points": 6}
        ]
    },
    {
        "id": 5,
        "tasks": [
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 4},
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 5},
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 6}
        ]
    },
    {
        "id": 6,
        "tasks": [
            {"description": "Obtain 15 beginner clue uniques", "points": 4},
            {"description": "Obtain 15 beginner clue uniques", "points": 5},
            {"description": "Obtain 15 beginner clue uniques", "points": 6}
        ]
    },
    {
        "id": 7,
        "tasks": [
            {"description": "Obtain 15 easy clue uniques", "points": 4},
            {"description": "Obtain 15 easy clue uniques", "points": 5},
            {"description": "Obtain 15 easy clue uniques", "points": 6}
        ]
    },
    {
        "id": 8,
        "tasks": [
            {"description": "Obtain 15 medium clue uniques", "points": 4},
            {"description": "Obtain 15 medium clue uniques", "points": 5},
            {"description": "Obtain 15 medium clue uniques", "points": 6}
        ]
    },
    {
        "id": 9,
        "tasks": [
            {"description": "Obtain 10 hard clue uniques", "points": 4},
            {"description": "Obtain 10 hard clue uniques", "points": 5},
            {"description": "Obtain 10 hard clue uniques", "points": 6}
        ]
    },
    {
        "id": 10,
        "tasks": [
            {"description": "Obtain a drop unique to a slayer boss", "points": 4},
            {"description": "Obtain a drop unique to a slayer boss", "points": 5},
            {"description": "Obtain a drop unique to a slayer boss", "points": 6}
        ]
    },
]

hard_task_set = [
    {
        "id": 1,
        "tasks": [
            {"description": "Defeat Obor 25 times", "points": 7},
            {"description": "Defeat Obor 30 times", "points": 8},
            {"description": "Defeat Obor 35 times", "points": 9}
        ]
    },
    {
        "id": 2,
        "tasks": [
            {"description": "Defeat Bryophyta 25 times", "points": 7},
            {"description": "Defeat Bryophyta 30 times", "points": 8},
            {"description": "Defeat Bryophyta 35 times", "points": 9}
        ]
    },
    {
        "id": 3,
        "tasks": [
            {"description": "Obtain 5 drops unique to wintertodt", "points": 7},
            {"description": "Obtain 5 drops unique to wintertodt", "points": 8},
            {"description": "Obtain 5 drops unique to wintertodt", "points": 9}
        ]
    },
    {
        "id": 4,
        "tasks": [
            {"description": "Obtain 5 drops unique to tempeross", "points": 7},
            {"description": "Obtain 5 drops unique to tempeross", "points": 8},
            {"description": "Obtain 5 drops unique to tempeross", "points": 9}
        ]
    },
    {
        "id": 5,
        "tasks": [
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 7},
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 8},
            {"description": "Obtain 5 drops unique to Guardians of the Rift", "points": 9}
        ]
    },
    {
        "id": 6,
        "tasks": [
            {"description": "Obtain 15 beginner clue uniques", "points": 7},
            {"description": "Obtain 15 beginner clue uniques", "points": 8},
            {"description": "Obtain 15 beginner clue uniques", "points": 9}
        ]
    },
    {
        "id": 7,
        "tasks": [
            {"description": "Obtain 15 easy clue uniques", "points": 7},
            {"description": "Obtain 15 easy clue uniques", "points": 8},
            {"description": "Obtain 15 easy clue uniques", "points": 9}
        ]
    },
    {
        "id": 8,
        "tasks": [
            {"description": "Obtain 15 medium clue uniques", "points": 7},
            {"description": "Obtain 15 medium clue uniques", "points": 8},
            {"description": "Obtain 15 medium clue uniques", "points": 9}
        ]
    },
    {
        "id": 9,
        "tasks": [
            {"description": "Obtain 10 hard clue uniques", "points": 7},
            {"description": "Obtain 10 hard clue uniques", "points": 8},
            {"description": "Obtain 10 hard clue uniques", "points": 9}
        ]
    },
    {
        "id": 10,
        "tasks": [
            {"description": "Obtain a drop unique to a slayer boss", "points": 7},
            {"description": "Obtain a drop unique to a slayer boss", "points": 8},
            {"description": "Obtain a drop unique to a slayer boss", "points": 9}
        ]
    },
]

boss_task_set = {
    1: ("Obtain a Purple from COX", 15),
    2: ("Obtain a Purple from TOA", 10),
    3: ("Obtain a Purple from TOB", 25),
    # Add more boss tasks here if needed
}

task_sets = {
    "easy": easy_task_set,  # Your easy tasks
    "medium": medium_task_set,  # Structure medium tasks similarly
    "hard": hard_task_set,  # Structure hard tasks similarly
}


def get_task_weights(wave):
    if wave < 10:
        return {"easy": 90, "medium": 9, "hard": 1}
    elif wave < 20:
        return {"easy": 70, "medium": 25, "hard": 5}
    elif wave < 30:
        return {"easy": 50, "medium": 40, "hard": 10}
    elif wave < 40:
        return {"easy": 30, "medium": 50, "hard": 20}
    elif wave < 50:
        return {"easy": 10, "medium": 60, "hard": 30}
    else:
        return {"easy": 5, "medium": 35, "hard": 60}


def select_task_for_team(difficulty, team):
    # Get the team's completed tasks for the difficulty
    completed_tasks = team.get("completed_tasks", {}).get(difficulty, {})

    available_tasks = []

    # Iterate over the tasks in the task set
    for task_info in task_sets[difficulty]:
        task_id = task_info["id"]
        task_levels = task_info["tasks"]

        # Get the highest level completed for this task
        completed_level = completed_tasks.get(task_id, -1)

        # Ensure completed_level is an integer
        if not isinstance(completed_level, int):
            completed_level = -1

        # Only add the task if the next level is not completed
        if completed_level + 1 < len(task_levels):
            available_tasks.append((difficulty, task_levels[completed_level + 1]["description"],
                                    task_levels[completed_level + 1]["points"], task_id, completed_level + 1))

    # If there are available tasks, randomly select one
    if available_tasks:
        return random.choice(available_tasks)

    # If no tasks are available (all levels completed), return None to trigger a re-roll
    return None

def generate_tasks(wave, team):
    tasks = []
    if wave % 10 == 0:
        # Boss wave, only one task
        task_id, task = random.choice(list(boss_task_set.items()))
        tasks.append(("boss", task[0], task[1], task_id, 0))
    else:
        weights = get_task_weights(wave)
        attempted_tasks = set()  # Keep track of tasks already assigned this wave

        for _ in range(3):  # Assuming you want 3 tasks per wave
            while True:
                difficulty = random.choices(
                    ["easy", "medium", "hard"],
                    weights=[weights["easy"], weights["medium"], weights["hard"]]
                )[0]
                selected_task = select_task_for_team(difficulty, team)

                # Re-roll until a valid and unique task is found
                if selected_task and (selected_task[3], selected_task[4]) not in attempted_tasks:
                    tasks.append(selected_task)
                    attempted_tasks.add((selected_task[3], selected_task[4]))  # Mark this task as assigned
                    break

    return tasks

@bot.command()
async def complete(ctx, team_name: str, task_number: int, member_str: str):
    global game_state
    try:
        print(f"Running !complete command: team_name={team_name}, task_number={task_number}, member_str={member_str}")

        team = next(
            (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
            None
        )
        if not team:
            await ctx.send(f"Team {team_name} does not exist.")
            return

        print(f"Team data: {team}")

        member = ctx.author
        is_team_captain = any(role.name == "Team Captain" for role in member.roles)
        is_admin = member.guild_permissions.administrator

        if not (is_team_captain or is_admin):
            await ctx.send(f"{member.mention}, you are not authorized to complete tasks for {team_name}. Only team captains or server administrators can do so.")
            return

        completed_tasks_count = sum(1 for t in team["tasks"] if "completed" in t)

        if completed_tasks_count >= 2 and team["tasks"][task_number - 1][0] != "boss":
            await ctx.send(f"{team_name} has already completed 2 tasks this wave. Progress: Complete {completed_tasks_count}/2 tasks to continue.")
            return

        if task_number < 1 or task_number > len(team["tasks"]):
            await ctx.send(f"Invalid task number. Please choose a number between 1 and {len(team['tasks'])}.")
            return

        try:
            task = team["tasks"][task_number - 1]
        except IndexError as e:
            logging.error(f"IndexError when accessing team tasks: {e}")
            print(f"Current task list: {team['tasks']}")
            await ctx.send(f"An error occurred while trying to access task number {task_number}.")
            return

        print(f"Task details: {task}")

        if "completed" in task:
            await ctx.send(f"Task '{task[1]}' has already been completed.")
            return

        points = task[2]
        double_points_info = team.get("double_points_task")
        if double_points_info:
            task_index = double_points_info["task_index"]
            deadline = datetime.fromisoformat(double_points_info["deadline"])

            if task_number - 1 == task_index and datetime.utcnow() <= deadline:
                points *= 2
                await ctx.send(f"**Double Points!** Task '{task[1]}' completed within the time limit. Points doubled to {points}.")
                del team["double_points_task"]

        try:
            member = await commands.MemberConverter().convert(ctx, member_str)
        except commands.BadArgument:
            await ctx.send(f"Could not find a member with the name or mention {member_str}. Please ensure the name or mention is correct.")
            return

        member_display_name = member.display_name

        task = list(task)
        task.append("completed")
        task.append(member_display_name)
        team["tasks"][task_number - 1] = tuple(task)

        print(f"Updated task: {task}")

        team["points"] += points
        team["members"].setdefault(member_display_name, 0)
        team["members"][member_display_name] += points

        difficulty = task[0]
        task_id = task[3]
        set_index = task[4]

        if difficulty not in team["completed_tasks"]:
            team["completed_tasks"][difficulty] = {}

        if task_id not in team["completed_tasks"][difficulty]:
            team["completed_tasks"][difficulty][task_id] = [None] * len(task_sets[difficulty])

        team["completed_tasks"][difficulty][task_id][set_index] = member_display_name

        save_game_state()

        completed_tasks_count += 1

        await ctx.send(f"Task '{task[1]}' completed by {member_display_name} from {team_name}! {points} points awarded. Progress: Complete {completed_tasks_count}/2 tasks to continue.")

        if completed_tasks_count >= 2 or task[0] == "boss":
            await ctx.send(f"{team_name} has completed the wave. Please use `!progress {team_name}` to continue to the next wave.")

    except IndexError as e:
        logging.error(f"Error in !complete command: {e}")
        await ctx.send(f"An error occurred while processing the command: {str(e)}")
    except Exception as e:
        logging.error(f"Error in !complete command: {e}")
        await ctx.send(f"An error occurred while processing the command: {str(e)}")

@complete.error
async def complete_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to use this command.")
    else:
        await ctx.send(f"An unexpected error occurred: {str(error)}")

@complete.error
async def complete_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to use this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

@complete.error
async def complete_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to use this command.")

@bot.command()
async def progress(ctx, team_name: str):
    global game_state
    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )
    if not team:
        await ctx.send(f"Team {team_name} does not exist.")
        return

    # Check if the user is a team captain or an administrator
    member = ctx.author
    is_team_captain = any(role.name == "Team Captain" for role in member.roles)
    is_admin = member.guild_permissions.administrator

    if not (is_team_captain or is_admin):
        await ctx.send(f"{member.mention}, you are not authorized to progress {team_name}. Only team captains or server administrators can do so.")
        return

    # Check if the team has completed enough tasks to progress
    completed_tasks = sum(1 for t in team["tasks"] if "completed" in t)
    if completed_tasks < 2 and not any(t[0] == "boss" for t in team["tasks"]):
        await ctx.send(f"{team_name} has not completed enough tasks to progress. Complete at least 2 tasks before using `!progress`.")
        return

    if team.get("shop_accessed", False):
        # Reset the shop_accessed flag if it’s preventing progress in a new wave
        await ctx.send(f"{team_name} has already accessed the shop in the previous wave. Resetting shop access to allow progression.")
        team["shop_accessed"] = False
        save_game_state()

    await ctx.send(f"{team_name}, you have completed the wave! Would you like to: \n1️⃣ Access the shop\n2️⃣ Continue to the next wave")

    def check(m):
        return m.author == ctx.author and m.content in ['1', '2']

    try:
        reply = await bot.wait_for('message', timeout=60.0, check=check)

        if reply.content == '1':
            available_items = get_random_shop_items(2)
            number_emojis = ["1️⃣", "2️⃣"]
            shop_message = "**Welcome to the shop! Here are the available items:**\n"
            for i, (item_id, item) in enumerate(available_items.items(), 1):
                shop_message += f"{number_emojis[i-1]} **{item['name']}** - {item['description']} (Cost: {item['cost']} points)\n"
            shop_message += "\nPlease enter the number of the item you'd like to purchase, or type `cancel` to exit."
            await ctx.send(shop_message)

            def shop_check(m):
                return m.author == ctx.author and (m.content in ['1', '2'] or m.content.lower() == "cancel")

            try:
                shop_reply = await bot.wait_for('message', timeout=60.0, check=shop_check)

                if shop_reply.content.lower() == "cancel":
                    await ctx.send(f"{team_name} has exited the shop. Moving to the next wave.")
                else:
                    selected_index = int(shop_reply.content) - 1
                    item = list(available_items.values())[selected_index]

                    if team["points"] >= item["cost"]:
                        team["points"] -= item["cost"]
                        team["purchases"].append(item["name"])
                        save_game_state()
                        await ctx.send(f"{team_name} has purchased **{item['name']}** for {item['cost']} points!")
                    else:
                        await ctx.send(f"{team_name} does not have enough points to purchase **{item['name']}**.")

            except asyncio.TimeoutError:
                await ctx.send(f"{team_name}, no response received. Exiting the shop and moving to the next wave.")

        # Mark the shop as accessed and advance the wave
        team["shop_accessed"] = True
        team["wave"] += 1
        team["tasks"] = generate_tasks(team["wave"], team)
        save_game_state()
        await ctx.send(f"{team_name} has moved to Wave {team['wave']}!")

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        tasks_message = f"**{team_name}, here are your tasks for Wave {team['wave']}:**\n"
        for i, task in enumerate(team["tasks"], 1):
            tasks_message += f"{number_emojis[i-1]} {task[1]} (Points: {task[2]})\n"
        await ctx.send(tasks_message)

    except asyncio.TimeoutError:
        await ctx.send(f"{team_name}, no response received. Automatically continuing to the next wave.")
        team["shop_accessed"] = True
        team["wave"] += 1
        team["tasks"] = generate_tasks(team["wave"], team)
        save_game_state()
        await ctx.send(f"{team_name} has moved to Wave {team['wave']}!")

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        tasks_message = f"**{team_name}, here are your tasks for Wave {team['wave']}:**\n"
        for i, task in enumerate(team["tasks"], 1):
            tasks_message += f"{number_emojis[i-1]} {task[1]} (Points: {task[2]})\n"
        await ctx.send(tasks_message)

@bot.command()
async def inventory(ctx, team_name: str):
    global game_state
    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )
    if not team:
        await ctx.send(f"Team {team_name} does not exist.")
        return

    purchases = team.get("purchases", [])

    if not purchases:
        await ctx.send(f"{team_name} has not purchased any items yet.")
    else:
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        inventory_message = f"**{team_name}'s Inventory:**\n"
        for i, item in enumerate(purchases, 1):
            inventory_message += f"{number_emojis[i-1]} {item}\n"
        await ctx.send(inventory_message)

@bot.command()
async def use(ctx, team_name: str, item_number: int):
    global game_state
    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (
                    data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )
    if not team:
        await ctx.send(f"Team {team_name} does not exist.")
        return

    # Check if the user is a team captain or an administrator
    member = ctx.author
    is_team_captain = any(role.name == "Team Captain" for role in member.roles)
    is_admin = member.guild_permissions.administrator

    if not (is_team_captain or is_admin):
        await ctx.send(f"{member.mention}, you are not authorized to use items for {team_name}. Only team captains or server administrators can do so.")
        return

    inventory = team.get("purchases", [])

    if not inventory:
        await ctx.send(f"{team_name} has no items in their inventory.")
        return

    if item_number < 1 or item_number > len(inventory):
        await ctx.send(f"Invalid item number. Please choose a number between 1 and {len(inventory)}.")
        return

    item = inventory[item_number - 1]

    if item.lower() == "monkey's paw":
        await ctx.send(f"{team_name} used **Monkey's Paw**! All tasks will be re-rolled with a higher chance of getting harder tasks.")

        # Re-roll all tasks with a higher weight for harder tasks
        new_tasks = []
        for task in team["tasks"]:
            difficulty = task[0]  # Get the original task's difficulty
            # Adjust weights to favor harder tasks
            weights = {"easy": 10, "medium": 30, "hard": 60}
            new_difficulty = random.choices(["easy", "medium", "hard"], weights=[weights["easy"], weights["medium"], weights["hard"]])[0]
            new_task = select_task_for_team(new_difficulty, team)
            new_tasks.append(new_task)

        team["tasks"] = new_tasks
        save_game_state()

        # Notify the team of their new tasks
        number_emojis = ["1️⃣", "2️⃣", "3️⃣"]
        tasks_message = f"**{team_name}, your tasks have been re-rolled:**\n"
        for i, task in enumerate(team["tasks"], 1):
            tasks_message += f"{number_emojis[i-1]} {task[1]} (Points: {task[2]})\n"
        await ctx.send(tasks_message)

    elif item.lower() == "rickrolling stew":
        await ctx.send(f"{team_name} used **RickRolling Stew**! Smells like a new task!")

        if team["tasks"]:
            reroll_index = random.randint(0, len(team["tasks"]) - 1)
            old_task = team["tasks"][reroll_index]
            difficulty = old_task[0]
            new_task = select_task_for_team(difficulty, team)
            team["tasks"][reroll_index] = new_task

            await ctx.send(f"Task **{old_task[1]}** has been re-rolled to **{new_task[1]}** (Points: {new_task[2]})")
        else:
            await ctx.send(f"{team_name} has no tasks to re-roll.")

    # Handle other items similarly

    # Remove the item from the team's inventory
    inventory.pop(item_number - 1)
    save_game_state()
    await ctx.send(f"{item} has been removed from {team_name}'s inventory.")

@use.error
async def use_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Try all you might, but you can't use nothing!")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


@bot.command()
@commands.has_permissions(administrator=True)
async def set_teams(ctx, num_teams: int):
    global game_started, game_state

    if game_started:
        await ctx.send("The game has already started! You cannot set teams after the game has started.")
        return

    game_state = {
        f"Team{i + 1}": {
            "wave": 1,
            "tasks": [],
            "points": 0,
            "gp": 0,
            "members": {},
            "purchases": [],
            "completed_tasks": {},
            "custom_name": None
        }
        for i in range(num_teams)
    }

    save_game_state()
    await ctx.send(f"{num_teams} teams have been set with names: {', '.join(game_state.keys())}!")


@bot.command()
@commands.has_permissions(administrator=True)
async def set_name(ctx, team: str, name: str):
    global game_state

    # Convert the team name to lower case for case-insensitive matching
    team_key = next((key for key in game_state if key.lower() == team.lower()), None)

    if not team_key:
        await ctx.send(f"Team '{team}' does not exist.")
        return

    # Check if the new custom name is already taken (case-insensitive)
    if any(data['custom_name'] and data['custom_name'].lower() == name.lower() for data in game_state.values()):
        await ctx.send(f"The name '{name}' is already taken. Please choose a different name.")
        return

    # Set the custom name for the team
    game_state[team_key]['custom_name'] = name
    save_game_state()
    await ctx.send(f"{team_key} is now named '{name}'!")

@bot.command()
@commands.has_permissions(administrator=True)
async def assign_captain(ctx, *members: discord.Member):
    """
    Assign the "Team Captain" role to the specified members.
    Only users with administrator permissions can run this command.
    """
    # Define the role name
    role_name = "Team Captain"

    # Get the role object from the guild
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    # Check if the role exists
    if not role:
        await ctx.send(f"The role '{role_name}' does not exist. Please create it first.")
        return

    # Assign the role to each member
    for member in members:
        if role not in member.roles:
            await member.add_roles(role)
            await ctx.send(f"{member.display_name} has been assigned the '{role_name}' role.")
        else:
            await ctx.send(f"{member.display_name} already has the '{role_name}' role.")

    # Confirm the completion
    await ctx.send("All specified members have been assigned the 'Team Captain' role.")

@bot.command()
async def assign_members(ctx, team_name: str, *members: discord.Member):
    global game_state
    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )

    if not team:
        await ctx.send(f"Team {team_name} does not exist.")
        return

    for member in members:
        # Use the member's nickname if available, otherwise use their username
        member_display_name = member.nick if member.nick else member.name
        team["members"][member_display_name] = team["members"].get(member_display_name, 0)

    save_game_state()
    await ctx.send(f"Members assigned to {team_name}: {', '.join(team['members'].keys())}")


# Global variable to track whether the game has started
game_started = False

# Load game state when the bot starts
game_state = load_game_state()


@bot.command()
async def start(ctx):
    global game_started, game_state

    if game_started:
        await ctx.send("The game has already started! You cannot start it again.")
        return

    # Mark the game as started
    game_started = True

    for team_name, team in game_state.items():
        team["wave"] = 1
        team["tasks"] = generate_tasks(team["wave"], team)

    save_game_state()

    await ctx.send("Game has started! Wave 1 has begun for all teams!")

    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for team_name, team in game_state.items():
        tasks_message = f"**{team_name}, here are your tasks for Wave 1:**\n"
        for i, task in enumerate(team["tasks"], 1):
            tasks_message += f"{number_emojis[i - 1]} {task[1]} (Points: {task[2]})\n"
        await ctx.send(tasks_message)


async def continue_wave(ctx, team_name: str):
    global game_state
    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )

    if not team:
        await ctx.send(f"Team {team_name} does not exist.")
        return

    team["wave"] += 1
    team["tasks"] = generate_tasks(team["wave"], team)
    save_game_state()
    await ctx.send(f"{team_name} has moved to Wave {team['wave']}!")

@bot.command()
async def points(ctx, team_name: str = None):
    global game_state
    if team_name:
        team = next(
            (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
            None
        )

        if not team:
            await ctx.send(f"Team {team_name} does not exist.")
            return

        original_name = next(key for key, data in game_state.items() if data == team)
        display_name = f"{original_name} ({team['custom_name']})" if team['custom_name'] else original_name
        response = f"{display_name} - Wave {team['wave']}:\n"

        for task in team["tasks"]:
            status = "~~" if "completed" in task else ""
            response += f"{status}{task[1]} (Points: {task[2]}){status}\n"
    else:
        response = "All Teams:\n"
        for name, team_data in game_state.items():
            display_name = f"{name} ({team_data['custom_name']})" if team_data['custom_name'] else name
            response += f"{display_name} - Wave {team_data['wave']} - Points: {team_data['points']}\n"

    await ctx.send(response)

import logging

@bot.command()
async def current(ctx, team_name: str = None):
    global game_state
    response = ""

    number_emojis = ["1️⃣", "2️⃣", "3️⃣"]

    if team_name:
        team = next(
            (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
            None
        )
        if not team:
            await ctx.send(f"Team {team_name} does not exist.")
            return

        original_name = next(key for key, data in game_state.items() if data == team)
        display_name = f"{original_name} ({team['custom_name']})" if team['custom_name'] else original_name

        response += f"**{display_name}** - **Wave {team['wave']}**:\n"
        if team["tasks"]:
            is_boss_wave = any(task[0] == "boss" for task in team["tasks"])

            if is_boss_wave:
                response += "  **Boss Wave:** Complete the boss task to proceed!\n"
            else:
                completed_count = sum(1 for task in team["tasks"] if "completed" in task)
                response += f"  **Progress:** {completed_count}/2 tasks completed to continue\n"

                # Auto-correct the shop_accessed flag if necessary
                if completed_count < 2 and team.get("shop_accessed", False):
                    team["shop_accessed"] = False
                    save_game_state()
                    logging.debug(f"Shop access reset for team {display_name}.")

                for idx, task in enumerate(team["tasks"], 1):
                    status = "~~" if "completed" in task else ""
                    emoji = number_emojis[idx - 1] if idx <= len(number_emojis) else f"{idx}."
                    response += f"  {emoji} {status}**{task[1]}** (Points: {task[2]}){status}\n"
        else:
            response += "  No tasks assigned yet.\n"

    else:
        for name, team_data in game_state.items():
            display_name = f"{name} ({team_data['custom_name']})" if team_data['custom_name'] else name
            response += f"**{display_name}** - **Wave {team_data['wave']}**:\n"

            if team_data["tasks"]:
                is_boss_wave = any(task[0] == "boss" for task in team_data["tasks"])

                if is_boss_wave:
                    response += "  **Boss Wave:** Complete the boss task to proceed!\n"
                else:
                    completed_count = sum(1 for task in team_data["tasks"] if "completed" in task)
                    response += f"  **Progress:** {completed_count}/2 tasks completed to continue\n"

                    # Auto-correct the shop_accessed flag if necessary
                    if completed_count < 2 and team_data.get("shop_accessed", False):
                        team_data["shop_accessed"] = False
                        save_game_state()
                        logging.debug(f"Shop access reset for team {display_name}.")

                    for idx, task in enumerate(team_data["tasks"], 1):
                        status = "~~" if "completed" in task else ""
                        emoji = number_emojis[idx - 1] if idx <= len(number_emojis) else f"{idx}."
                        response += f"  {emoji} {status}**{task[1]}** (Points: {task[2]}){status}\n"
            else:
                response += "  No tasks assigned yet.\n"

            response += "\n"

    # Check if response is empty and handle it
    if not response.strip():
        response = "No information available to display."

    await ctx.send(response)

@bot.command()
async def members(ctx):
    global game_state
    response = "### **Teams and their Members** ###\n\n"

    for team_name, team_data in game_state.items():
        # Display the team name, with custom name if available
        display_name = f"{team_name} ({team_data['custom_name']})" if team_data['custom_name'] else team_name
        response += f"**{display_name}**\n"

        if team_data["members"]:
            response += "```\n"  # Start a code block for the member list
            for member_name in team_data["members"]:
                # Attempt to find the member by their username
                member = discord.utils.get(ctx.guild.members, name=member_name)
                if member:
                    member_display_name = member.nick if member.nick else member.name
                    response += f"{member_display_name}\n"
                else:
                    response += f"{member_name}\n"
            response += "```\n"  # End the code block
        else:
            response += "No members assigned.\n"

        response += "\n"  # Add some space between teams

    await ctx.send(response)


@bot.command()
async def gp(ctx):
    global game_state
    gp_message = "**Total GP Earned by Teams:**\n"
    for team_name, team_data in game_state.items():
        display_name = f"{team_name} ({team_data['custom_name']})" if team_data['custom_name'] else team_name
        gp_message += f"{display_name}: {team_data['gp']} GP\n"
    await ctx.send(gp_message)

from discord.ext import commands

@bot.command()
@commands.has_permissions(administrator=True)
async def reset_tasks(ctx, team_name: str):
    global game_state
    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )
    if not team:
        await ctx.send(f"Team {team_name} does not exist.")
        return

    # Track the total points to remove
    points_to_remove = 0

    # Iterate through tasks and mark completed tasks as incomplete, removing points
    for task in team["tasks"]:
        if "completed" in task:
            # Subtract the points from the team
            points_to_remove += task[2]
            # Remove the "completed" status from the task
            task.remove("completed")

    # Subtract the points from the team's total points
    team["points"] -= points_to_remove

    # Ensure the team's points do not go below zero
    team["points"] = max(0, team["points"])

    # Update the completed tasks tracking
    team["completed_tasks"] = {difficulty: {} for difficulty in task_sets.keys()}

    save_game_state()

    await ctx.send(f"Tasks for {team_name} have been reset. {points_to_remove} points were removed. You can now complete tasks or use !progress.")

@reset_tasks.error
async def reset_tasks_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to use this command.")

@bot.command()
async def commandlist(ctx):
    general_commands = [
        "`!inventory <team_name>` - View the current inventory of a team.",
        "`!members` - List all teams and their members.",
        "`!gp` - View the total GP earned by each team.",
        "`!current <team_name>` - Show the current tasks and their completion status for a team.",
        "`!completed <team_name> [<member_name>]` - Show completed tasks for a team or a specific member.",
        "`!completed_all` - Show completed tasks for all teams.",
        "`!mvp` - Show the top 3 players who have earned the most points.",
        "`!points <team_name>` - View the wave number and tasks for a specific team."
    ]

    captain_commands = [
        "`!progress <team_name>` - Progress to the next wave after completing 2 tasks.",
        "`!complete <team_name> <task_number> <member_name>` - Mark a task as completed.",
        "`!use <team_name> <item_number>` - Use an item from the team's inventory.",
        "`!set_name <team> <name>` - Set a custom name for your team.",
        "`!assign_members <team_name> <members...>` - Assign members to a team."
    ]

    admin_commands = [
        "`!set_teams <num_teams>` - Initialize the game with a specified number of teams.",
        "`!reset_tasks <team_name>` - Reset the tasks for a team, removing their progress.",
        "`!start` - Start the game, initializing the first wave of tasks."
    ]

    embed = discord.Embed(
        title="Command List",
        description="Below is a list of available commands for players, captains, and administrators.",
        color=discord.Color.blue()
    )

    embed.add_field(name="General Commands", value="\n".join(general_commands), inline=False)
    embed.add_field(name="Captain Commands", value="\n".join(captain_commands), inline=False)
    embed.add_field(name="Admin Commands", value="\n".join(admin_commands), inline=False)

    embed.set_footer(text="Use the appropriate commands according to your role. Happy gaming!")

    await ctx.send(embed=embed)

@bot.command()
async def mvp(ctx):
    """Show the top 3 players who have earned the most points."""
    if not game_started:
        await ctx.send("The game has not started yet. Please use !start to start the game.")
        return

    try:
        # Calculate points for each player
        player_points = defaultdict(int)
        for team in game_state.values():
            for member_name, points in team["members"].items():
                # Prefer using display names consistently
                player_points[member_name] += points

        # Find the top players based on total points
        top_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)[:3]

        if not top_players:
            await ctx.send("No players have earned any points yet.")
            return

        # Prepare response
        response = "🏆🌟 **Top 3 MVPs of the Game** 🌟🏆\n\n"

        medals = ["🥇", "🥈", "🥉"]
        previous_points = None
        medal_index = 0
        lines = []
        tied_players = []

        for i, (player_name, points) in enumerate(top_players):
            # Extra safety: Remove @ from the start if it exists
            player_name = player_name.lstrip('@')

            # Escape markdown special characters to avoid mentions
            player_name = discord.utils.escape_markdown(player_name)

            if previous_points is not None and points == previous_points:
                tied_players.append(player_name)
            else:
                if tied_players:
                    if len(tied_players) > 1:
                        lines.append(
                            f"{current_medal} **{'** and **'.join(tied_players)}** have all earned {previous_points:.2f} points and are tied!")
                    else:
                        lines.append(f"{current_medal} **{tied_players[0]}**: {previous_points:.2f} points")
                    tied_players = []

                if medal_index >= len(medals):
                    break

                current_medal = medals[medal_index]
                tied_players.append(player_name)
                previous_points = points
                medal_index += 1

        if tied_players:
            if len(tied_players) > 1:
                lines.append(
                    f"{current_medal} **{'** and **'.join(tied_players)}** have all earned {previous_points:.2f} points and are tied!")
            else:
                lines.append(f"{current_medal} **{tied_players[0]}**: {previous_points:.2f} points")

        response += "\n\n".join(lines)
        await ctx.send(response)
    except Exception as e:
        logging.error(f"Error in mvp command: {e}")
        await ctx.send(f"An error occurred while processing the command: {str(e)}")


@bot.command()
async def completed(ctx, team_name: str, member: str = None):
    global game_state, task_sets

    team = next(
        (data for key, data in game_state.items() if key.lower() == team_name.lower() or (data['custom_name'] and data['custom_name'].lower() == team_name.lower())),
        None
    )

    if not team:
        await ctx.send(f"Team '{team_name}' not found.")
        return

    response = f"### **Completed Tasks for {team_name}** ###\n\n"
    display_name = f"{team_name} ({team['custom_name']})" if team['custom_name'] else team_name
    team_points = team.get("points", 0)

    response += f"**Total Points: {team_points}**\n"

    if member:
        member_display_name = None
        for m_name in team['members'].keys():
            if member.lower() in m_name.lower():
                member_display_name = m_name
                break

        if not member_display_name:
            await ctx.send(f"Member '{member}' not found in team '{team_name}'.")
            return

        member_completed_tasks = []

        for difficulty, tasks in team['completed_tasks'].items():
            for task_id_str, task_levels in tasks.items():
                task_id = int(task_id_str)
                for level_index, completed_by in enumerate(task_levels):
                    if completed_by == member_display_name:
                        task_details = task_sets[difficulty][task_id - 1]["tasks"][level_index]
                        task_description = task_details["description"]
                        task_points = task_details["points"]
                        member_completed_tasks.append(f"• {task_description} (Points: {task_points})")

        member_points = team["members"].get(member_display_name, 0)
        response += f"**Points for {member_display_name}: {member_points}**\n"
        response += "```\n"

        if member_completed_tasks:
            response += "\n".join(member_completed_tasks)
        else:
            response += f"No completed tasks found for {member_display_name}."
        response += "\n```"

    else:
        completed_tasks = []

        for difficulty, tasks in team['completed_tasks'].items():
            for task_id_str, task_levels in tasks.items():
                task_id = int(task_id_str)
                for level_index, completed_by in enumerate(task_levels):
                    if completed_by:
                        task_details = task_sets[difficulty][task_id - 1]["tasks"][level_index]
                        task_description = task_details["description"]
                        task_points = task_details["points"]
                        completed_tasks.append(f"• {task_description} (Points: {task_points}) - Completed by {completed_by}")

        response += "```\n"
        if completed_tasks:
            response += "\n".join(completed_tasks)
        else:
            response += "No completed tasks found."
        response += "\n```"

    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await ctx.send(response[i:i + 2000])
    else:
        await ctx.send(response)

@bot.command()
async def completed_all(ctx):
    global game_state, task_sets

    for team_name, team_data in game_state.items():
        response = f"### **Completed Tasks for {team_name}** ###\n\n"
        display_name = f"{team_name} ({team_data['custom_name']})" if team_data['custom_name'] else team_name
        team_points = team_data.get("points", 0)

        response += f"**Total Points: {team_points}**\n"
        response += "```\n"  # Start a code block for better formatting
        completed_tasks = []

        # Iterate through the team's completed tasks
        for difficulty, tasks in team_data['completed_tasks'].items():
            for task_id_str, task_levels in tasks.items():
                task_id = int(task_id_str)  # Convert task_id to integer
                for level_index, completed_by in enumerate(task_levels):
                    if completed_by:  # Check if the task was completed
                        task_details = task_sets[difficulty][task_id - 1]["tasks"][level_index]
                        task_description = task_details["description"]
                        task_points = task_details["points"]
                        completed_tasks.append(f"• {task_description} (Points: {task_points}) - Completed by {completed_by}")

        # Append completed tasks to the response
        if completed_tasks:
            response += "\n".join(completed_tasks)
        else:
            response += "No completed tasks found."
        response += "\n```"  # End the code block

        # Send the response in chunks if it's too long
        if len(response) > 2000:
            for i in range(0, len(response), 2000):
                await ctx.send(response[i:i+2000])
        else:
            await ctx.send(response)

        await ctx.send(".")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
