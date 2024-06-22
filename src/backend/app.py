import json
from flask import Flask, request, jsonify
import sqlite3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

RIOT_KEY = os.getenv('RIOT_KEY')
REGION = "americas"
RIOT_URL = "api.riotgames.com"

app = Flask(__name__)

def init_db():
   db_connection = sqlite3.connect('users.db')
   with app.open_resource('schema.sql') as f:
      db_connection.executescript(f.read().decode('utf8'))
   return db_connection

def get_db_connection():
    connection = sqlite3.connect('users.db')
    return connection

@app.route('/add', methods=['POST'])
def add():
   req = request.json
   discord_account, username, tag = req["discord_account"], req["username"], req["tag"]
   request_url = f"https://{REGION}.{RIOT_URL}/riot/account/v1/accounts/by-riot-id/{username}/{tag}?api_key={RIOT_KEY}"
   response = requests.get(request_url)

   if response.status_code != 200:
      return jsonify({"error": f"Riot API request failed with status {response.status_code}"}), response.status_code

   account_data = response.json()
   if not isinstance(account_data, dict) or "puuid" not in account_data:
      return jsonify({"error": "Invalid response format from Riot API"}), 500

   conn = get_db_connection()
   cursor = conn.cursor()

   try:
      query = '''INSERT INTO users (discord_account, username, tag, puuid) VALUES (?, ?, ?, ?)'''
      values = (discord_account, username, tag, account_data["puuid"])
      cursor.execute(query, values)
      conn.commit()
      return jsonify({"message": "User added successfully"}), 200

   except sqlite3.Error as e:
      conn.rollback()
      return jsonify({"error": str(e)}), 500

   finally:
      cursor.close()
      conn.close()
      return req, 200

@app.route('/remove', methods=['POST'])
def remove_user():
   req = request.json
   discord_account, username, tag = req["discord_account"], req["username"], req["tag"]
   conn = get_db_connection()
   cursor = conn.cursor()

   try:
      cursor.execute("SELECT * FROM users WHERE discord_account = ? AND username = ? AND tag = ?", (discord_account, username, tag))
      record = cursor.fetchone()
      print(record)
      if record:
         cursor.execute("DELETE FROM users WHERE discord_account = ? AND username = ? AND tag = ?", (discord_account, username, tag))
         conn.commit()  # Committing the changes
         response_message = "User removed successfully."
         status_code = 200
      else:
         response_message = "User not found."
         status_code = 404

   except sqlite3.Error as e:
      conn.rollback()  # Rolling back in case of error
      response_message = f"Database error: {e}"
      status_code = 500

   finally:
      cursor.close()
      conn.close()

   return jsonify({"message": response_message}), status_code

@app.route('/list')
def list_users():
   conn = get_db_connection()
   cursor = conn.cursor()
    
   # Fetch both username and tag in a single query
   cursor.execute("SELECT username, tag FROM users")
   user_data = cursor.fetchall()
    
   cursor.close()
   conn.close()
    
   # Format the username and tag pairs
   formatted_user_data = [f"{username}#{tag}" for username, tag in user_data]
    
   return jsonify(formatted_user_data)

@app.route('/recent', methods=['POST'])
def get_recents():
   req = request.json
   discord_account, username, tag = req["discord_account"], req["username"], req["tag"]
   
   conn = get_db_connection()
   cursor = conn.cursor()
   
   cursor.execute("SELECT puuid FROM users WHERE discord_account = ? AND username = ? AND tag = ?", (discord_account, username, tag))
   record = cursor.fetchone()
   if record: 
      puuid = record[0]
   else:
      puuid = None

   request_url = f"https://{REGION}.{RIOT_URL}/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=10&api_key={RIOT_KEY}"
   print(request_url)
   response = requests.get(request_url)

   if response.status_code != 200:
      return jsonify({"error": f"Riot API request failed with status {response.status_code}"}), response.status_code

   match_ids = response.json()
   result = []

   for match in match_ids:
      match_url = f"https://{REGION}.{RIOT_URL}/tft/match/v1/matches/{match}?api_key={RIOT_KEY}"
      print(match_url)
      current_match_response = requests.get(match_url)
      data = current_match_response.json()
      for participants in data["info"]["participants"]:
         if participants["puuid"] == puuid:
            result.append(participants["placement"])
            break
   return result
   
if __name__ == '__main__':
   init_db()
   app.run()
