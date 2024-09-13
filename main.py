import discord
from discord import app_commands
import random
import asyncio
import os
import re
import requests
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
                "content": "Você é um assistente útil. Responda com respostas curtas."
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

# Função para analisar links
def analisar_link(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return "Este link é válido com o seguinte conteúdo: " + response.text[:200]
        else:
            return "Não foi possível acessar o conteúdo do link."
    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar o link: {e}"

# Detecta URLs nas mensagens
url_pattern = r'(https?://[^\s]+)'

@aclient.event
async def on_message(message):
    if message.author == aclient.user:
        return

    # Analisar links nas mensagens
    urls = re.findall(url_pattern, message.content)
    for url in urls:
        link_analysis = analisar_link(url)
        await message.channel.send(f"Análise do link {url}: {link_analysis}")

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

# Comando para obter uma piada
@tree.command(name='piada', description='Receba uma piada aleatória')
async def joke(interaction: discord.Interaction):
    response = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
    piada = response.json().get("joke", "Não consegui encontrar uma piada agora.")
    await interaction.response.send_message(piada, ephemeral=True)

# Comando para tocar música
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'noplaylist': True,
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@tree.command(name='play', description='Toque uma música do YouTube')
async def play(interaction: discord.Interaction, url: str):
    if interaction.user.voice is None:
        await interaction.response.send_message("Você precisa estar em um canal de voz para tocar música.")
        return
    
    voice_channel = interaction.user.voice.channel
    if not aclient.voice_clients:
        vc = await voice_channel.connect()
    else:
        vc = aclient.voice_clients[0]
    
    info = ytdl.extract_info(url, download=False)
    source = discord.FFmpegPCMAudio(info['url'])
    
    vc.play(source)
    await interaction.response.send_message(f"Tocando: {info['title']}")

aclient.run('')  # Insira o token do bot aqui
