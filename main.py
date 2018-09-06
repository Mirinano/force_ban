import asyncio
import discord
import time
import datetime
import os

client = discord.Client()

master_cmd_id = "" #ここに管理者連絡室内の横断BAN実行専用チャンネルのID

stop_time = 60 #実行受理から緊急停止までの猶予☆☆

# force_ban, force_un_ban
done_number = 3 #実行に必要な⭕の数
cancel_number = 3 #中止に必要な❌の数
timeout = 300 # timeoutまでの秒数

# past_ban, past_unban
done_number_past = 2 #実行に必要な⭕の数
cancel_number_past = 2 #中止に必要な❌の数
timeout_past = 300 # timeoutまでのデフォルト秒数☆

#過去のBANユーザーについてログファイルから取得。
with open("ban_user_log.txt", "r", encoding="utf-8") as f:
    ban_user_log = set([s.strip() for s in f.readlines()])

@asyncio.coroutine
def force_ban(user_id, server_id, delete_message_days=1):
    yield from client.http.ban(user_id, server_id, delete_message_days)

@asyncio.coroutine
def force_unban(user_id, server_id):
    yield from client.http.unban(user_id, server_id)

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
    # 情報を格納
    msg_ch = message.channel
    msg_ch_name = message.channel.name
    author_name = message.author.name
    author_id = message.author.id
    content = message.content
    message_time = message.timestamp
    message_time_str = message_time.strftime("%Y/%m/%d %H:%M:%S") + "(UTS)"
    msg_time_ym = message_time.strftime("%Y-%m")
    file_dir = ""
    file_name = "message_log/" + msg_time_ym + "/" + msg_ch_name + ".txt"
    file_dir = os.path.dirname(file_name)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    else:
        pass
    with open(file_name, "a", encoding="utf-8") as log_f:
        log_f.write("送信者: " + author_name + "(ID: " + author_id + ")\n")
        log_f.write("送信時間: " + message_time_str +"\n")
        log_f.write("内容:\n" + content + "\n")
        log_f.write("----------\n")
    if message.channel.id == master_cmd_id:
        if (message.content.startswith("$force_ban") or message.content.startswith("$force_unban") or message.content.startswith("$past_ban") or message.content.startswith("$past_unban")):
            #処理番号用
            with open("accept_count.txt", "r", encoding="utf-8") as f:
                accept_count = f.read()
            next_count = int(accept_count) + 1
            with open("accept_count.txt", "w", encoding="utf-8") as f:
                f.write(str(next_count))
        else:
            pass
        if (message.content.startswith("$force_ban") or message.content.startswith("$force_unban")):
            if message.content.startswith("$force_ban"):
                deal = "ban"
                deal_content = "BAN"
            elif message.content.startswith("$force_unban"):
                deal = "unban"
                deal_content = "BANを解除"
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
            content = "次のユーザーをこのBOTを導入している次のサーバーすべてで" + deal_content +"します。\n"
            ban_user_info = "名前: " + ban_user.name + "\nメンション: <@" + ban_user_id + ">\n"
            ban_server = "```" + "\n".join(servers_name_list) + "```\n"
            action_message = "⭕の数が" + str(done_number) + "つに達すると実行されます。❌の数が" + str(cancel_number) + "つに達すると拒否されます。\nまた、5分間リアクションの追加がない場合でも拒否されます。\n"
            accept_count_content = "受付番号: " + accept_count
            check_content = content + ban_user_info + ban_server + action_message + accept_count_content
            check_msg = await client.send_message(send_ch, check_content)
            await client.add_reaction(check_msg, "⭕")
            await client.add_reaction(check_msg, "❌")
            reaction_count = dict()
            reaction_count["done"] = 1 #初期化
            reaction_count["cancel"] = 1
            result = "cancel" #デフォルトでは実行しないにしておく。
            loop = True
            while loop:
                target_reaction = await client.wait_for_reaction(message=check_msg, timeout=timeout)
                if target_reaction == None: #タイムアウト
                    err_content = "タイムアウトエラー。" + deal_content +"は実施されませんでした。\n" + accept_count_content
                    loop = None
                    result = "err"
                else:
                    if target_reaction.user != client.user:
                        if target_reaction.reaction.emoji == "⭕":
                            reaction_user = await client.get_reaction_users(target_reaction.reaction)
                            reaction_count["done"] = len(reaction_user)
                            if reaction_count["done"] == done_number:
                                loop = None
                                result = "done"
                            else:
                                pass
                        elif target_reaction.reaction.emoji == "❌":
                            reaction_user = await client.get_reaction_users(target_reaction.reaction)
                            reaction_count["cancel"] = len(reaction_user)
                            if reaction_count["cancel"] == cancel_number:
                                loop = None
                                result = "cancel"
                            else:
                                pass
                        else:
                            await client.remove_reaction(check_msg, target_reaction.reaction.emoji, target_reaction.user)
            if result == "err": #タイムアウトエラー
                await client.send_message(send_ch, err_content)
            elif result == "cancel": #キャンセル
                await client.send_message(message.channel, deal_content + "をキャンセルしました。\n" + accept_count_content)
            elif result == "done": #実行。
                await client.send_message(send_ch, deal_content + "を1分後に実行します。\n実行前に緊急停止するときには「!stop」と書き込んでください。\n" + accept_count_content)
                count_down_start = datetime.datetime.now()
                stop_time = 60
                while True:
                    stop_msg = await client.wait_for_message(timeout=stop_time, content="!stop", channel=message.channel)
                    if ((stop_msg == None) or (stop_time <= 0)):
                        await client.send_message(send_ch, deal_content + "を実行します。\n" + accept_count_content)
                        done_server = list()
                        fail_server = list()
                        if deal == "ban":
                            for sil in servers_id_list:
                                try:
                                    await force_ban(user_id=ban_user_id, server_id=sil, delete_message_days=1)
                                    time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                    done_server.append(servers_dict_list[sil])
                                except:
                                    fail_server.append(servers_dict_list[sil])
                            result_content = "横断BANが完了しました。\n実行できたサーバー\n```\n" + "\n".join(done_server) + "\n```\n失敗したサーバー\n```\n" + "\n".join(fail_server) + "\n```\n" + accept_count_content
                            await client.send_message(send_ch, result_content)
                            ban_user_log.add(ban_user_id) #集合にログを追加しておく。
                            with open("ban_user_log.txt", "a", encoding="utf-8") as f: #ログとして保存
                                f.write(ban_user_id + "\n")
                        elif deal == "unban":
                            for sil in servers_id_list:
                                try:
                                    await force_unban(user_id=ban_user_id, server_id=sil)
                                    time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                    done_server.append(servers_dict_list[sil])
                                except:
                                    fail_server.append(servers_dict_list[sil])
                            result_content = "横断BANの解除が完了しました。\n実行できたサーバー\n```\n" + "\n".join(done_server) + "\n```\n失敗したサーバー\n```\n" + "\n".join(fail_server) + "\n```\n" + accept_count_content
                            await client.send_message(send_ch, result_content)
                            ban_user_log.discard(ban_user_id) #集合にログを追加しておく。
                            with open("ban_user_log.txt", "w", encoding="utf-8") as f: #ログから削除する
                                f.write("\n".join(list(ban_user_log)))
                        else:
                            await client.send_message(send_ch, "【実行エラー】\n<@391943696809197568> プログラムコードに異常が起きている可能性があります。BOTを強制停止(サーバーを停止)させてください。\n" + accept_count_content) #ミリナノにメンションで警告
                        break
                    else: # "!stop"ではなかった。~~なんだよ！~~
                        elapsed_time = datetime.datetime.now() - count_down_start #経過時間を計測
                        stop_time = stop_time - int(elapsed_time.seconds)
        elif (message.content.startswith("$past_ban") or message.content.startswith("$past_unban")): #過去にさかのぼってログにあるすべてのアカウントをBAN(解除)します。
            if message.content.startswith("$past_ban"):
                deal = "ban"
                deal_content = "BAN"
            elif message.content.startswith("$past_unban"):
                deal = "unban"
                deal_content = "BANを解除"
            send_ch = message.channel
            server_id = message.content.split("\n").pop(1) # IDを取り出す。
            server_name = ""
            for s in client.servers:
                if server_id == s.id:
                    server_name = s.name
                    server = s
                    break
                else:
                    pass
            for sm in server.members:
                if sm == message.author:
                    server_permissions = sm.server_permissions
                    break
                else:
                    pass
            if server_permissions.ban_members:
                content = "これまでに<#447403257044926465>に報告されているアカウントを次のサーバーで" + deal_content + "します。\n"
                ban_server = "```\n" + server_name + "\n```"
                action_message = "⭕を押すと実行されます。❌を押すと拒否されます。\nまた、5分間リアクションの追加がない場合でも拒否されます。\n"
                accept_count_content = "受付番号: " + accept_count
                check_content = content + ban_server + action_message + accept_count_content
                check_msg = await client.send_message(send_ch, check_content)
                await client.add_reaction(check_msg, "⭕")
                await client.add_reaction(check_msg, "❌")
                reaction_count = dict()
                reaction_count["done"] = 1 #初期化
                reaction_count["cancel"] = 1
                result = "cancel" #デフォルトでは実行しないにしておく。
                timeout_past = 300
                loop = True
                while loop:
                    start_time = datetime.datetime.now()
                    target_reaction = await client.wait_for_reaction(message=check_msg, timeout=timeout_past)
                    if target_reaction == None: #タイムアウト
                        err_content = "タイムアウトエラー。" + deal_content +"は実施されませんでした。\n" + accept_count_content
                        loop = None
                        result = "err"
                    else:
                        if target_reaction.user != client.user:
                            for sm in server.members:
                                if sm == target_reaction.user:
                                    server_permissions = sm.server_permissions
                                    break
                                else:
                                    pass
                            if server_permissions.ban_members:
                                if target_reaction.reaction.emoji == "⭕":
                                    reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                    reaction_count["done"] = len(reaction_user)
                                    if reaction_count["done"] == done_number_past:
                                        loop = None
                                        result = "done"
                                    else:
                                        pass
                                elif target_reaction.reaction.emoji == "❌":
                                    reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                    reaction_count["cancel"] = len(reaction_user)
                                    if reaction_count["cancel"] == cancel_number_past:
                                        loop = None
                                        result = "cancel"
                                    else:
                                        pass
                                else:
                                    await client.remove_reaction(check_msg, target_reaction.reaction.emoji, target_reaction.user)
                            else: #権限のない人がスタンプを押した。
                                elapsed_time = datetime.datetime.now() - start_time #経過時間を計測
                                timeout_past = timeout_past - int(elapsed_time.seconds)
                                if timeout_past > 0:
                                    err_msg = "<@" + target_reaction.user.id + ">\nあなたは「" + server_name + "」でBAN権限を持っていないため、実行/キャンセルをすることができません。\n" + str(timeout_past) + "秒後までにBAN権限を持っているユーザーが実行/キャンセルを選択してください。\n"
                                    await client.remove_reaction(check_msg, target_reaction.reaction.emoji, target_reaction.user)
                                    await client.send_message(send_ch, err_msg + accept_count_content)
                                else: #時間切れ
                                    pass
                if result == "err": #タイムアウトエラー
                    await client.send_message(send_ch, err_content)
                elif result == "cancel": #キャンセル
                    await client.send_message(send_ch, deal_content + "をキャンセルしました。\n" + accept_count_content)
                elif result == "done": #実行
                    await client.send_message(send_ch, deal_content + "を1分後に実行します。\n実行前に緊急停止するときには「!stop」と書き込んでください。\n" + accept_count_content)
                    count_down_start = datetime.datetime.now()
                    stop_time = 60
                    while True:
                        stop_msg = await client.wait_for_message(timeout=stop_time, content="!stop", channel=message.channel)
                        if ((stop_msg == None) or (stop_time <= 0)):
                            await client.send_message(send_ch, deal_content + "を実行します。\n" + accept_count_content)
                            done_user = list()
                            fail_user = list()
                            if deal == "ban":
                                for bul in ban_user_log:
                                    ban_user = await client.get_user_info(user_id=bul)
                                    try:
                                        await force_ban(user_id=bul, server_id=server_id, delete_message_days=1)
                                        time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                        done_user.append(ban_user.name)
                                    except:
                                        fail_user.append(ban_user.name)
                            elif deal == "unban":
                                for bul in ban_user_log:
                                    ban_user = await client.get_user_info(user_id=bul)
                                    try:
                                        await force_unban(user_id=bul, server_id=server_id)
                                        time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                        done_user.append(ban_user.name)
                                    except:
                                        fail_user.append(ban_user.name)
                            result_content = deal_content + "が完了しました。\n実行したユーザー\n```\n" + "\n".join(done_user) + "\n```\n失敗したユーザー\n```\n" + "\n".join(fail_user) + "\n```\n" + accept_count_content
                            await client.send_message(send_ch, result_content)
                            break
                        else: # "!stop"ではなかった。
                            elapsed_time = datetime.datetime.now() - count_down_start #経過時間を計測
                            stop_time = stop_time - int(elapsed_time.seconds)
            else: # コマンド投稿者がその鯖でBAN権限を持っていなかった。
                await client.send_message(send_ch, "<@" + message.author.id + ">\nあなたは「" + server_name + "」でのBAN権限を持っていないため、このコマンドが使えません。")
        else:
            pass

client.run("Token")
