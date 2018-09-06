import asyncio
import discord

client = discord.Client()

master_cmd_id = "" #ここに管理者連絡室内の横断BAN実行専用チャンネルのID

done_number = 5 #実行に必要な⭕の数
cancel_number = 3 #中止に必要な❌の数

@asyncio.coroutine
def force_ban(user_id, server_id, delete_message_days=1):
    yield from client.http.ban(user_id, server_id, delete_message_days)

# ログイン
@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("--------")

# 横断BAN機能本文
@client.event
async def on_message(message):
    if message.channel.id == master_cmd_id:
        if message.content.startswith("$force_ban"):
            send_ch = message.channel
            ban_user_id = message.content.split("\n").pop(1) # IDを取り出す。
            ban_user = await client.get_user_info(user_id=ban_user_id)
            servers_id_list = list()
            servers_name_list = list()
            servers_dict_list = dict() #初期化
            for servers in client.servers:
                servers_id_list.append(servers.id)
                servers_name_list.append(servers.name)
                servers_dict_list[servers.id] = servers.name
            content = "次のユーザーをこのBOTを導入している次のサーバーすべてでBANします。\n"
            ban_user_info = "名前: " + ban_user.name + "\nメンション: <@" + ban_user_id + ">\n"
            ban_server = "```" + "\n".join(servers_name_list) + "```\n"
            action_message = "⭕の数が" + str(done_number) + "つに達すると実行されます。❌の数が" + str(cancel_number) + "つに達すると拒否されます。\nまた、5分間リアクションの追加がない場合でも拒否されます。"
            check_content = content + ban_user_info + ban_server + action_message
            check_msg = await client.send_message(send_ch, check_content)
            await client.add_reaction(check_msg, "⭕")
            await client.add_reaction(check_msg, "❌")
            reaction_count = dict()
            reaction_count["done"] = 1 #初期化
            reaction_count["cancel"] = 1
            result = "cancel" #デフォルトでは実行しないにしておく。
            loop = True
            while loop:
                target_reaction = await client.wait_for_reaction(message=check_msg, timeout=300)
                print(target_reaction.reaction.emoji)
                if target_reaction.user != client.user:
                    if target_reaction == None: #タイムアウト
                        err_content = "タイムアウトエラー。横断BANは実施されませんでした。"
                        loop = None
                        result = "err"
                    elif target_reaction.reaction.emoji == "⭕":
                        reaction_count["done"] += 1
                        if reaction_count["done"] == done_number:
                            loop = None
                            result = "done"
                        else:
                            pass
                    elif target_reaction.reaction.emoji == "❌":
                        reaction_count["cancel"] += 1
                        if reaction_count["cancel"] == cancel_number:
                            loop = None
                            result = "cancel"
                        else:
                            pass
                    else:
                        await client.remove_reaction(check_msg, target_reaction[0], target_reaction[1])
                else:
                    pass
            if result == "err": #タイムアウトエラー
                await client.send_message(send_ch, err_content)
            elif result == "cancel": #キャンセル
                await client.send_message(message.channel, "横断BANをキャンセルしました。")
            elif result == "done": #横断BANを実施。
                await client.send_message(send_ch, "横断BANを実行します。")
                done_server = list()
                fail_server = list()
                for sil in servers_id_list:
                    try:
                        await force_ban(user_id=ban_user_id, server_id=sil, delete_message_days=1)
                        done_server.append(servers_dict_list[sil])
                    except:
                        fail_server.append(servers_dict_list[sil])
                result_content = "横断BANが完了しました。\n実行できたサーバー\n```\n" + "\n".join(done_server) + "\n```\n失敗したサーバー\n```\n" + "\n".join(fail_server) + "\n```"
                await client.send_message(send_ch, result_content)
                
client.run("Token")
