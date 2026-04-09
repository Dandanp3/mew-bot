import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from server.models.serverModel import serverModel
import discord
from discord.ext import commands

load_dotenv()

class ServerController:
    def __init__(self, db):
        self.collection = db['servers']
        
    async def get_chat_id(self, server_id: int):
        print(f"DEBUG: Buscando ID: {server_id} | Tipo: {type(server_id)}")
        
        doc_teste = await self.collection.find_one({})
        if doc_teste:
            print(f"DEBUG: Documento encontrado no banco: {doc_teste['id']} | Tipo no Banco: {type(doc_teste['id'])}")

        server_data = await self.collection.find_one({"id": server_id})
        return server_data.get("chat") if server_data else None
            
    
    async def server_register(self, server_id: int):
        # procurar o server no banco
        server_exists = await self.collection.find_one({"id": server_id})
        
        # se for none, nao existe
        if not server_exists:
            new_server_data = serverModel(
                id=server_id,
                chat=None
            )
            await self.collection.insert_one(new_server_data.to_dict())
            print(f"Servidor: {server_id} registrado no banco de dados.")
        else:
            print(f"ℹServidor: {server_id} já existe no banco de dados.")
        
        
    
    async def save_chat(self, server_id: int, chat_id: int):
        await self.server_register(server_id)
        
        # Depois atualiza o chat_id
        result = await self.collection.update_one(
            {"id": server_id},
            {"$set": {"chat": chat_id}},
            upsert=True
        )
        print(f"Chat ID {chat_id} salvo para o servidor {server_id}")
        return result.modified_count > 0
    
    async def get_server(self, server_id: int):
        return await self.collection.find_one({"id": server_id})
    
    async def get_all_servers(self):
        return await self.collection.find().to_list(None)