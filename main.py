import discord
from discord import app_commands
import random
import asyncio
import os
from groq import Groq

# Inicialize o cliente Groq com sua chave API
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Configurações gerais do bot
class client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False  # Evita sincronizar os comandos mais de uma vez
        self.conversations = {}  # Armazena as conversas em andamento

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:  # Sincroniza comandos globalmente
            await tree.sync()
            self.synced = True
        print(f"Entramos como {self.user}.")

    async def timeout_conversation(self, user_id):
        await asyncio.sleep(60)  # Espera 1 minuto
        if user_id in self.conversations:
            del self.conversations[user_id]  # Remove a conversa após o timeout


aclient = client()
tree = app_commands.CommandTree(aclient)

# Comando de Teste
@tree.command(name='teste', description='Testando') 
async def slash0(interaction: discord.Interaction):
    await interaction.response.send_message("Estou funcionando!", ephemeral=True)

# Comando para rolar um dado D20
@tree.command(name='D20', description='Jogue o dado D20 e descubra a sua sorte') 
async def slash2(interaction: discord.Interaction):
    numero = random.randint(1, 20)
    await interaction.response.send_message(f"O Dado parou em: {numero}", ephemeral=True)

# Detecta mensagens enviadas no servidor
@aclient.event
async def on_message(message):
    if message.author == aclient.user:
        return

    if message.content.startswith("!chat"):
        user_id = message.author.id
        if user_id not in aclient.conversations:
            aclient.conversations[user_id] = [{
                "role": "system",
                "content": "You are a helpful assistant. You reply with very short answers."
            }]

        user_message = message.content[len("!chat "):]
        aclient.conversations[user_id].append({"role": "user", "content": user_message})

        response = client_groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=aclient.conversations[user_id],
            max_tokens=100,
            temperature=1.2
        )

        reply = response.choices[0].message.content
        await message.channel.send(reply)

        aclient.conversations[user_id].append({"role": "assistant", "content": reply})

        # Reinicia o temporizador para timeout da conversa
        if user_id in aclient.conversations:
            await asyncio.sleep(1)  # Para evitar conflito de tempo
            asyncio.create_task(aclient.timeout_conversation(user_id))

# Comando para kickar um usuário
@tree.command(
    guild=discord.Object(id=id_do_servidor),
    name='kick',
    description='Expulsar um usuário do servidor')
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Não especificado"):
    if interaction.user.guild_permissions.kick_members:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} foi expulso por {interaction.user.mention} por: {reason}")
    else:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)

# Comando para banir um usuário
@tree.command(
    guild=discord.Object(id=id_do_servidor),
    name='ban',
    description='Banir um usuário do servidor')
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Não especificado"):
    if interaction.user.guild_permissions.ban_members:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} foi banido por {interaction.user.mention} por: {reason}")
    else:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)

# Comando para mutar um usuário (precisa de uma role "Muted")
@tree.command(
    guild=discord.Object(id=id_do_servidor),
    name='mute',
    description='Mutar um usuário no servidor')
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "Não especificado"):
    muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if muted_role is None:
        muted_role = await interaction.guild.create_role(name="Muted")

        for channel in interaction.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)

    if interaction.user.guild_permissions.manage_roles:
        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"{member.mention} foi mutado por {interaction.user.mention} por: {reason}")
    else:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)

aclient.run('')  # Insira o token do bot aqui
