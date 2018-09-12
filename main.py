import discord
import asyncio
import time
import datetime
import os
import copy

client = discord.Client()

master_server_id = "" #ここに管理者連絡室内のサーバーID
master_cmd_id = "" #ここに管理者連絡室内の横断BAN実行専用チャンネルのID

stop_time = 60 #実行受理から緊急停止までの猶予

# force_ban, force_un_ban
timeout = 300 # timeoutまでの秒数

# past_ban, past_unban
done_number_past = 2 #実行に必要な⭕の数
cancel_number_past = 2 #中止に必要な❌の数
timeout_past = 300 # timeoutまでのデフォルト秒数☆

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
    print("ban_serverに参加していないサーバーが含まれていないかチェックする。")
    client_server = set()
    for s in client.servers:
        client_server.add(s.id)
    with open("ban_server.txt", "r", encoding="utf-8") as f:
        ban_server = set([s.strip() for s in f.readlines()])
    new_ban_server = ban_server & client_server
    with open("ban_server.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(list(new_ban_server)) + "\n")
    print("チェックし除外しました。")

# 横断BAN機能本文
@client.event
async def on_message(message):
    # 情報を格納
    msg_ch = message.channel
    msg_ch_name = message.channel.name
    author_name = message.author.name
    author_id = message.author.id
    content = message.content
    msg_server_name = message.server.name
    msg_server_id = message.server.id
    user_roles = message.author.roles
    message_time = message.timestamp
    message_time_str = message_time.strftime("%Y/%m/%d %H:%M:%S") + "(UTS)"
    msg_time_ym = message_time.strftime("%Y-%m")
    file_dir = ""
    file_name = "message_log/" + msg_time_ym + "/" + msg_server_name + "/" + msg_ch_name + ".txt"
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
    if message.content.startswith("$add_server"):
        if message.author.server_permissions.manage_server:
            with open("ban_server.txt", "a", encoding="utf-8") as f:
                f.write(msg_server_id + "\n")
            done_content = msg_server_name + "を横断BANを実行するサーバーに追加しました。\n除外するときは「$remove_server」と書き込んでください。"
            await client.send_message(msg_ch, done_content)
        else:
            await client.semd_message(msg_ch, "あなたはこのコマンドを実行する権限を持っていません。")
    elif message.content.startswith("$remove_server"):
        if message.author.server_permissions.manage_server:
            with open("ban_server.txt", "r", encoding="utf-8") as f:
                ban_server = set([s.strip() for s in f.readlines()])
            ban_server.discard(msg_server_id)
            with open("ban_server.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(list(ban_server)) + "\n")
            done_content = msg_server_name + "を横断BANを実行するサーバーから除外しました。\n追加するときは「$add_server」と書き込んでください。"
            await client.send_message(msg_ch, done_content)
        else:
            await client.send_message(msg_ch, "あなたはこのコマンドを実行する権限を持っていません。")
    elif message.content.startswith("$help"):
        if message.channel.id == master_cmd_id:
            with open("help.txt", "r", encoding="utf-8") as f:
                help_msg = f.read()
        else:
            with open("help_other.txt", "r", encoding="utf-8") as f:
                help_msg = f.read()
        await client.send_message(msg_ch, help_msg)
    elif message.channel.id == master_cmd_id:
        if message.content.startswith("$change_msg"):
            if "Manager" in [r.name for r in user_roles]:
                content_list = content.split("\n")
                content_list.pop(0) #一行目の「$change_msg」を削除。
                cmd_line = content_list.pop(0)
                if cmd_line in ["help", "help_other"]:
                    change_content = "\n".join(content_list)
                    #変更を反映し、変更前と後についてのログをmsg_change_logフォルダ内に保存する。
                    file_name = cmd_line + ".txt"
                    with open(file_name, "r", encoding="utf-8") as f:
                        befor_content = f.read()
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(change_content)
                    log_file_name = "msg_change_log/" + cmd_line + ".txt"
                    with open(log_file_name, "a", encoding="utf-8") as log_f:
                        log_f.write(message_time_str + "に" + author_name + "が" + cmd_line + "を次のように変更しました。\n")
                        log_f.write("変更前:\n" + befor_content + "\n")
                        log_f.write("変更後:\n" + change_content + "\n")
                        log_f.write("----------\n")
                    #変更について報告。
                    await client.send_message(msg_ch, cmd_line + "を次のように変更しました。\n変更前:\n" + befor_content + "\n変更後:\n" + change_content)
                else:
                    await client.send_message(msg_ch, "そのようなメッセージはありません。\n定義されているメッセージは「help」と「help_other」です。")
            else:
                await client.send_message(msg_ch, "あなたをはこのコマンドを使用する権限がありません。Managerのみが使用できます。")
        elif message.content.startswith("$change_number"):
            if "Manager" in [r.name for r in user_roles]:
                content_list = content.split("\n")
                content_list.pop(0) #一行目の「$change_number」を削除。
                err_check = True
                err_content = ""
                try:
                    change_num = content_list.pop(0)
                    if change_num in ["done_number", "cancel_number"]:
                        pass
                    else:
                        err_check = False
                        err_content = "2行目に指定した値が間違っています。\n指定できるのは「done_number」か「cancel_number」です。"
                except:
                    err_check = False
                    err_content = "2行目が未指定です。"
                if err_check:
                    try:
                        new_number = content_list.pop(0)
                    except:
                        err_check = False
                        err_content = "3行目が未指定です。"
                    if err_check:
                        if int(new_number) < 3:
                            new_number = "3"
                            revision_content = "\n※指定された数が3未満だったため、3に変更しました。"
                        else:
                            revision_content = ""
                        file_name = change_num + ".txt"
                        with open(file_name, "w", encoding="utf-8") as f:
                            f.write(new_number)
                        if change_num == "done_number":
                            result = "実行に"
                        else:
                            result = "拒否に"
                        result_content = result + "必要な人数を" + new_number + "人に変更しました。" + revision_content
                        await client.send_message(msg_ch, result_content)
                    else:
                        await client.send_message(msg_ch, err_content)
                else:
                    await client.send_message(msg_ch, err_content)
            else:
                await client.send_message(msg_ch, "あなたをはこのコマンドを使用する権限がありません。Managerのみが使用できます。")
        elif message.content.startswith("$server_list"):
            server_list = list()
            all_server = list()
            with open("ban_server.txt", "r", encoding="utf-8") as f:
                ban_server = set([s.strip() for s in f.readlines()])
            for s in ban_server:
                server = client.get_server(s)
                server_list.append(server.name)
            for s in client.servers:
                all_server.append(s.name)
            send_content = "BOTの参加しているサーバーは次の通りです。\n```" + "\n".join(all_server) + "\n```\n横断BAN対象に登録されているサーバーは次の通りです。\n```\n" + "\n".join(server_list) + "\n```"
            await client.send_message(msg_ch, send_content)
        elif (message.content.startswith("$force_ban") or message.content.startswith("$force_unban") or message.content.startswith("$past_ban") or message.content.startswith("$past_unban") or message.content.startswith("$ban")):
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
                deal_check = False
            elif message.content.startswith("$force_unban"):
                deal = "unban"
                deal_content = "BANを解除"
                deal_check = True
            send_ch = message.channel
            err_check = True
            err_content = ""
            try:
                ban_user_id = message.content.split("\n").pop(1) # IDを取り出す。
            except:
                err_check = False
                err_content = "コマンドの2行目が未指定です。"
            if err_check:
                try:
                    ban_user = await client.get_user_info(user_id=ban_user_id)
                except:
                    err_check = False
                    err_content = "存在しないユーザーIDです。"
                if err_check:
                    baned_user_list = await client.get_bans(message.server)
                    if ((ban_user in baned_user_list) and (deal == "ban")):
                        deal_check = True
                    else:
                        pass
                    if deal_check:
                        ban_server_name = list() #初期化
                        ban_server_dict = dict() #初期化
                        with open("ban_server.txt", "r", encoding="utf-8") as f:
                            ban_server = set([s.strip() for s in f.readlines()])
                        for s in ban_server:
                            ban_server_info = client.get_server(id=s)
                            ban_server_name.append(ban_server_info.name)
                            ban_server_dict[ban_server_info.id] = ban_server_info.name
                        with open("done_number.txt", "r", encoding="utf-8") as f:
                            done_number = int(f.read())
                        with open("cancel_number.txt", "r", encoding="utf-8") as f:
                            cancel_number = int(f.read())
                        content = "次のユーザーをこのBOTを導入している次のサーバーすべてで" + deal_content +"します。\n"
                        ban_user_info = "名前: " + ban_user.name + "\nメンション: <@" + ban_user_id + ">\n"
                        ban_server_content = "```" + "\n".join(ban_server_name) + "```\n"
                        action_message = "⭕の数が" + str(done_number) + "つに達すると実行されます。❌の数が" + str(cancel_number) + "つに達すると拒否されます。\nまた、5分間リアクションの追加がない場合でも拒否されます。\n"
                        accept_count_content = "受付番号: " + accept_count
                        check_content = content + ban_user_info + ban_server_content + action_message + accept_count_content
                        check_msg = await client.send_message(send_ch, check_content)
                        await client.add_reaction(check_msg, "⭕")
                        await client.add_reaction(check_msg, "❌")
                        # これまでの情報をここで過去ログ化
                        file_directory = "ban_log/" + accept_count + "_force-" + deal
                        if not os.path.exists(file_directory):
                            os.makedirs(file_directory)
                        else:
                            pass
                        file_name = file_directory + "/detail.txt"
                        with open(file_name, "a", encoding="utf-8") as f:
                            f.write("受付番号: " + accept_count + "\n")
                            f.write("受付時間: " + message_time_str + "\n")
                            f.write(deal_content + "対象者\n")
                            f.write("名前: " + ban_user.name + "\nID: " + ban_user_id + "\n\n")
                            f.write("コマンド起動者: " + message.author.name + "\n")
                        reaction_count = dict()
                        reaction_count["done"] = 1 #初期化
                        reaction_count["cancel"] = 1
                        result = "cancel" #デフォルトでは実行しないにしておく。
                        last_done_user = {client.user}
                        last_cancel_user = {client.user}
                        done_user = ""
                        cancel_user = ""
                        result_dict = dict()
                        deal_dict = dict()
                        result_dict["done"] = list()
                        result_dict["cancel"] = list()
                        loop = True
                        while loop:
                            target_reaction = await client.wait_for_reaction(message=check_msg, timeout=timeout)
                            if target_reaction == None: #タイムアウト
                                err_content = "タイムアウトエラー。" + deal_content +"は実施されませんでした。\n" + accept_count_content
                                loop = False
                                result = "err"
                            else:
                                if target_reaction.user != client.user:
                                    if target_reaction.reaction.emoji == "⭕":
                                        reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                        #ログ機能
                                        add_user = set(reaction_user).difference(last_done_user)
                                        remove_user = last_done_user.difference(set(reaction_user))
                                        deal_dict["add_user"] = ",".join([u.name for u in add_user])
                                        deal_dict["remove_user"] = ",".join([u.name for u in remove_user])
                                        deal_dict["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "(UTS)"
                                        done_user = "\n".join([u.name for u in reaction_user])
                                        deal_dict["count"] = str(len(reaction_user))
                                        result_dict["done"].append(copy.deepcopy(deal_dict))
                                        last_done_user = set(reaction_user) #更新
                                        reaction_count["done"] = len(reaction_user)
                                        if reaction_count["done"] == done_number:
                                            loop = None
                                            result = "done"
                                        else:
                                            pass
                                    elif target_reaction.reaction.emoji == "❌":
                                        reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                        #ログ機能
                                        add_user = set(reaction_user).difference(last_cancel_user)
                                        remove_user = last_cancel_user.difference(set(reaction_user))
                                        deal_dict["add_user"] = ",".join([u.name for u in add_user])
                                        deal_dict["remove_user"] = ",".join([u.name for u in remove_user])
                                        deal_dict["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "(UTS)"
                                        cancel_user = "\n".join([u.name for u in reaction_user])
                                        deal_dict["count"] = str(len(reaction_user))
                                        result_dict["cancel"].append(copy.deepcopy(deal_dict))
                                        last_cancel_user = set(reaction_user) #更新
                                        reaction_count["cancel"] = len(reaction_user)
                                        if reaction_count["cancel"] == cancel_number:
                                            loop = False
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
                            while True:
                                stop_msg = await client.wait_for_message(timeout=stop_time, content="!stop", channel=message.channel)
                                if stop_msg == None:
                                    await client.send_message(send_ch, deal_content + "を実行します。\n" + accept_count_content)
                                    done_server = list()
                                    fail_server = list()
                                    if deal == "ban":
                                        for sil in ban_server:
                                            try:
                                                await force_ban(user_id=ban_user_id, server_id=sil, delete_message_days=1)
                                                time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                                done_server.append(ban_server_dict[sil])
                                            except:
                                                fail_server.append(ban_server_dict[sil])
                                        result_content = "横断BANが完了しました。\n実行できたサーバー\n```\n" + "\n".join(done_server) + "\n```\n失敗したサーバー\n```\n" + "\n".join(fail_server) + "\n```\n" + accept_count_content
                                        await client.send_message(send_ch, result_content)
                                        file_name = file_directory + "/ban_log.txt"
                                        with open(file_name, "a", encoding="utf-8") as f:
                                            f.write(deal_content + "対象者\n")
                                            f.write("名前: " + ban_user.name + "\nID: " + ban_user_id + "\n\n")
                                            f.write("コマンド起動者: " + message.author.name + "\n")
                                            f.write("実行者: " + done_user + "\n")
                                            f.write("拒否者: " + cancel_user + "\n")
                                            f.write("実行サーバー:\n" + "\n  ".join(done_server) + "\n")
                                            f.write("失敗したサーバー:\n" + "\n  ".join(fail_server) + "\n")
                                    elif deal == "unban":
                                        for sil in ban_server:
                                            try:
                                                await force_unban(user_id=ban_user_id, server_id=sil)
                                                time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                                done_server.append(ban_server_dict[sil])
                                            except:
                                                fail_server.append(ban_server_dict[sil])
                                        result_content = "横断BANの解除が完了しました。\n実行できたサーバー\n```\n" + "\n".join(done_server) + "\n```\n失敗したサーバー\n```\n" + "\n".join(fail_server) + "\n```\n" + accept_count_content
                                        await client.send_message(send_ch, result_content)
                                        file_name = file_directory + "/unban_log.txt"
                                        with open(file_name, "a", encoding="utf-8") as f:
                                            f.write(deal_content + "対象者\n")
                                            f.write("名前: " + ban_user.name + "\nID: " + ban_user_id + "\n\n")
                                            f.write("コマンド起動者: " + message.author.name + "\n")
                                            f.write("実行者: " + done_user + "\n")
                                            f.write("拒否者: " + cancel_user + "\n")
                                            f.write("実行サーバー:\n" + "\n  ".join(done_server) + "\n")
                                            f.write("失敗したサーバー:\n" + "\n  ".join(fail_server) + "\n")
                                    else:
                                        await client.send_message(send_ch, "【実行エラー】\n<@391943696809197568> プログラムコードに異常が起きている可能性があります。BOTを強制停止(サーバーを停止)させてください。\n" + accept_count_content) #ミリナノにメンションで警告
                                    break
                                else: # "!stop"だ！
                                    result = "emergency_stop"
                                    await client.send_message(send_ch, "すべての処理を強制終了します。\n" + accept_count_content)
                                    break
                        else:
                            pass
                        # リアクションログを保存する。
                        file_name = file_directory + "/reaction_log.txt"
                        with open(file_name, "a", encoding="utf-8") as f:
                            f.write("最終的アクション: " + result + "\n\n")
                            for rc in ["done", "cancel"]:
                                f.write(rc + "ボタン\n\n")
                                for r in result_dict[rc]:
                                    f.write("時間: " + r["time"] + "\n")
                                    f.write("追加者: " + r["add_user"] + "\n")
                                    f.write("削除者: " + r["remove_user"] + "\n")
                                    f.write("カウント:" + r["count"] + "\n")
                                    f.write("-----------------\n")
                                f.write("\n")
                    else:
                        await client.send_message(msg_ch, "該当のユーザーは管理者連絡室でBANされていないユーザーです。\n横断BANの実行を中止します。")
                else:
                    await client.send_message(send_ch, err_content)
            else:
                await client.send_message(send_ch, err_content)
        elif (message.content.startswith("$past_ban") or message.content.startswith("$past_unban")): #過去にさかのぼってログにあるすべてのアカウントをBAN(解除)します。
            if message.content.startswith("$past_ban"):
                deal = "ban"
                deal_content = "BAN"
            elif message.content.startswith("$past_unban"):
                deal = "unban"
                deal_content = "BANを解除"
            send_ch = message.channel
            err_check = True
            err_content = ""
            try:
                server_id = message.content.split("\n").pop(1) # IDを取り出す。
            except:
                err_check = False
                err_content = "2行目が未指定です。"
            if err_check:
                server_name = ""
                for s in client.servers:
                    if server_id == s.id:
                        server_name = s.name
                        server = s
                        break
                    else:
                        pass
                if not server_name == "":
                    for sm in server.members:
                        if sm == message.author:
                            server_permissions = sm.server_permissions
                            break
                        else:
                            pass
                    if server_permissions.ban_members:
                        content = "このサーバーのBANリストに登録されているアカウントを次のサーバーで" + deal_content + "します。\n"
                        ban_server = "```\n" + server_name + "\n```"
                        action_message = "⭕を押すと実行されます。❌を押すと拒否されます。\nまた、5分間リアクションの追加がない場合でも拒否されます。\n"
                        accept_count_content = "受付番号: " + accept_count
                        check_content = content + ban_server + action_message + accept_count_content
                        check_msg = await client.send_message(send_ch, check_content)
                        await client.add_reaction(check_msg, "⭕")
                        await client.add_reaction(check_msg, "❌")
                        # これまでの情報をここで過去ログ化
                        file_directory = "ban_log/" + accept_count + "_past-" + deal
                        if not os.path.exists(file_directory):
                            os.makedirs(file_directory)
                        else:
                            pass
                        file_name = file_directory + "/detail.txt"
                        with open(file_name, "a", encoding="utf-8") as f:
                            f.write("受付番号: " + accept_count + "\n")
                            f.write("受付時間: " + message_time_str + "\n")
                            f.write(deal_content + "対象サーバー\n")
                            f.write("名前: " + server_name + "\nID: " + server_id + "\n\n")
                            f.write("コマンド起動者: " + message.author.name + "\n")
                        reaction_count = dict()
                        reaction_count["done"] = 1 #初期化
                        reaction_count["cancel"] = 1
                        result = "cancel" #デフォルトでは実行しないにしておく。
                        last_done_user = {client.user}
                        last_cancel_user = {client.user}
                        done_user = ""
                        cancel_user = ""
                        result_dict = dict()
                        deal_dict = dict()
                        result_dict["done"] = list()
                        result_dict["cancel"] = list()
                        timeout_past = 300
                        loop = True
                        while loop:
                            start_time = datetime.datetime.now()
                            target_reaction = await client.wait_for_reaction(message=check_msg, timeout=timeout_past)
                            if target_reaction == None: #タイムアウト
                                err_content = "タイムアウトエラー。" + deal_content +"は実施されませんでした。\n" + accept_count_content
                                loop = False
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
                                            #ログ機能
                                            add_user = set(reaction_user).difference(last_done_user)
                                            remove_user = last_done_user.difference(set(reaction_user))
                                            deal_dict["add_user"] = ",".join([u.name for u in add_user])
                                            deal_dict["remove_user"] = ",".join([u.name for u in remove_user])
                                            deal_dict["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "(UTS)"
                                            done_user = "\n".join([u.name for u in reaction_user])
                                            deal_dict["count"] = str(len(reaction_user))
                                            result_dict["done"].append(copy.deepcopy(deal_dict))
                                            last_done_user = set(reaction_user) #更新
                                            reaction_count["done"] = len(reaction_user)
                                            if reaction_count["done"] == done_number_past:
                                                loop = False
                                                result = "done"
                                            else:
                                                pass
                                        elif target_reaction.reaction.emoji == "❌":
                                            reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                            #ログ機能
                                            add_user = set(reaction_user).difference(last_cancel_user)
                                            remove_user = last_cancel_user.difference(set(reaction_user))
                                            deal_dict["add_user"] = ",".join([u.name for u in add_user])
                                            deal_dict["remove_user"] = ",".join([u.name for u in remove_user])
                                            deal_dict["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "(UTS)"
                                            cancel_user = "\n".join([u.name for u in reaction_user])
                                            deal_dict["count"] = str(len(reaction_user))
                                            result_dict["cancel"].append(copy.deepcopy(deal_dict))
                                            last_cancel_user = set(reaction_user) #更新
                                            reaction_count["cancel"] = len(reaction_user)
                                            if reaction_count["cancel"] == cancel_number_past:
                                                loop = False
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
                            while True:
                                stop_msg = await client.wait_for_message(timeout=stop_time, content="!stop", channel=message.channel)
                                if ((stop_msg == None) or (stop_time <= 0)):
                                    await client.send_message(send_ch, deal_content + "を実行します。\n" + accept_count_content)
                                    done_ban_user = list()
                                    fail_ban_user = list()
                                    if deal == "ban":
                                        baned_user = client.get_bans(message.server)
                                        for bul in baned_user:
                                            try:
                                                await force_ban(user_id=bul.id, server_id=server_id, delete_message_days=1)
                                                time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                                done_ban_user.append(ban_user.name)
                                            except:
                                                fail_ban_user.append(ban_user.name)
                                            file_name = file_directory + "/ban_log.txt"
                                            with open(file_name, "a", encoding="utf-8") as f:
                                                f.write(deal_content + "対象サーバー\n")
                                                f.write("名前: " + server_name + "\nID: " + server_id + "\n\n")
                                                f.write("コマンド起動者: " + message.author.name + "\n")
                                                f.write("実行者: " + done_user + "\n")
                                                f.write("拒否者: " + cancel_user + "\n")
                                                f.write("実行ユーザー:\n" + "\n  ".join(done_ban_user) + "\n")
                                                f.write("失敗したユーザー:\n" + "\n  ".join(fail_ban_user) + "\n")
                                    elif deal == "unban":
                                        baned_user = client.get_bans(message.server)
                                        for bul in ban_user:
                                            try:
                                                await force_unban(user_id=bul.id, server_id=server_id)
                                                time.sleep(0.5) #0.5秒止めてAPI制限に気を付ける
                                                done_ban_user.append(ban_user.name)
                                            except:
                                                fail_ban_user.append(ban_user.name)
                                            file_name = file_directory + "/unban_log.txt"
                                            with open(file_name, "a", encoding="utf-8") as f:
                                                f.write(deal_content + "対象サーバー\n")
                                                f.write("名前: " + server_name + "\nID: " + server_id + "\n\n")
                                                f.write("コマンド起動者: " + message.author.name + "\n")
                                                f.write("実行者: " + done_user + "\n")
                                                f.write("拒否者: " + cancel_user + "\n")
                                                f.write("実行ユーザー:\n" + "\n  ".join(done_ban_user) + "\n")
                                                f.write("失敗したユーザー:\n" + "\n  ".join(fail_ban_user) + "\n")
                                    result_content = deal_content + "が完了しました。\n実行したユーザー\n```\n" + "\n".join(done_ban_user) + "\n```\n失敗したユーザー\n```\n" + "\n".join(fail_ban_user) + "\n```\n" + accept_count_content
                                    await client.send_message(send_ch, result_content)
                                    break
                                else: # "!stop"だ！
                                    result = "emergency_stop"
                                    await client.send_message(send_ch, "すべての処理を強制終了します。\n" + accept_count_content)
                                    break
                        else:
                            pass
                        # リアクションログを保存する。
                        file_name = file_directory + "/reaction_log.txt"
                        with open(file_name, "a", encoding="utf-8") as f:
                            f.write("最終的アクション: " + result + "\n\n")
                            for rc in ["done", "cancel"]:
                                f.write(rc + "ボタン\n\n")
                                for r in result_dict[rc]:
                                    f.write("時間: " + r["time"] + "\n")
                                    f.write("追加者: " + r["add_user"] + "\n")
                                    f.write("削除者: " + r["remove_user"] + "\n")
                                    f.write("カウント:" + r["count"] + "\n")
                                    f.write("-----------------\n")
                                f.write("\n")
                    else: # コマンド投稿者がその鯖でBAN権限を持っていなかった。
                        await client.send_message(send_ch, "<@" + message.author.id + ">\nあなたは「" + server_name + "」でのBAN権限を持っていないため、このコマンドが使えません。")
                else:
                    err_content = "存在しないサーバーIDを指定したか、BOTが導入されていないサーバーを指定しています。"
                    await client.send_message(send_ch, err_content)
            else:
                await client.send_message(send_ch, err_content)
        elif message.content.startswith("$ban"): #管理者連絡室でBANします。
            send_ch = message.channel
            err_check = True
            err_content = ""
            try:
                ban_user_id = message.content.split("\n").pop(1) # IDを取り出す。
            except:
                err_check = False
                err_content = "2行目が未指定です。"
            if err_check:
                try:
                    ban_user = await client.get_user_info(user_id=ban_user_id)
                except:
                    err_check = False
                    err_content = "存在しないサーバーIDを指定しています。"
                if err_check:
                    if not ban_user_id in [u.name for u in message.server.members]:
                        content = "このサーバーので次のアカウントをBANします。\n"
                        ban_user_name = "```\n" + ban_user.name + "\n```"
                        action_message = "⭕を押すと実行されます。❌を押すと拒否されます。\nまた、5分間リアクションの追加がない場合でも拒否されます。\n"
                        accept_count_content = "受付番号: " + accept_count
                        check_content = content + ban_user_name + action_message + accept_count_content
                        check_msg = await client.send_message(send_ch, check_content)
                        await client.add_reaction(check_msg, "⭕")
                        await client.add_reaction(check_msg, "❌")
                        # これまでの情報をここで過去ログ化
                        file_directory = "ban_log/" + accept_count + "ban"
                        if not os.path.exists(file_directory):
                            os.makedirs(file_directory)
                        else:
                            pass
                        file_name = file_directory + "/detail.txt"
                        with open(file_name, "a", encoding="utf-8") as f:
                            f.write("受付番号: " + accept_count + "\n")
                            f.write("受付時間: " + message_time_str + "\n")
                            f.write("BAN対象ユーザー\n")
                            f.write("名前: " + ban_user.name + "\nID: " + ban_user_id + "\n\n")
                            f.write("コマンド起動者: " + message.author.name + "\n")
                        reaction_count = dict()
                        reaction_count["done"] = 1 #初期化
                        reaction_count["cancel"] = 1
                        result = "cancel" #デフォルトでは実行しないにしておく。
                        last_done_user = {client.user}
                        last_cancel_user = {client.user}
                        done_user = ""
                        cancel_user = ""
                        result_dict = dict()
                        deal_dict = dict()
                        result_dict["done"] = list()
                        result_dict["cancel"] = list()
                        timeout_past = 300
                        loop = True
                        while loop:
                            start_time = datetime.datetime.now()
                            target_reaction = await client.wait_for_reaction(message=check_msg, timeout=timeout_past)
                            if target_reaction == None: #タイムアウト
                                err_content = "タイムアウトエラー。BANは実施されませんでした。\n" + accept_count_content
                                loop = False
                                result = "err"
                            else:
                                if target_reaction.user != client.user:
                                    if target_reaction.reaction.emoji == "⭕":
                                        reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                        #ログ機能
                                        add_user = set(reaction_user).difference(last_done_user)
                                        remove_user = last_done_user.difference(set(reaction_user))
                                        deal_dict["add_user"] = ",".join([u.name for u in add_user])
                                        deal_dict["remove_user"] = ",".join([u.name for u in remove_user])
                                        deal_dict["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "(UTS)"
                                        done_user = "\n".join([u.name for u in reaction_user])
                                        deal_dict["count"] = str(len(reaction_user))
                                        result_dict["done"].append(copy.deepcopy(deal_dict))
                                        last_done_user = set(reaction_user) #更新
                                        reaction_count["done"] = len(reaction_user)
                                        if reaction_count["done"] == done_number_past:
                                            loop = False
                                            result = "done"
                                        else:
                                            pass
                                    elif target_reaction.reaction.emoji == "❌":
                                        reaction_user = await client.get_reaction_users(target_reaction.reaction)
                                        #ログ機能
                                        add_user = set(reaction_user).difference(last_cancel_user)
                                        remove_user = last_cancel_user.difference(set(reaction_user))
                                        deal_dict["add_user"] = ",".join([u.name for u in add_user])
                                        deal_dict["remove_user"] = ",".join([u.name for u in remove_user])
                                        deal_dict["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "(UTS)"
                                        cancel_user = "\n".join([u.name for u in reaction_user])
                                        deal_dict["count"] = str(len(reaction_user))
                                        result_dict["cancel"].append(copy.deepcopy(deal_dict))
                                        last_cancel_user = set(reaction_user) #更新
                                        reaction_count["cancel"] = len(reaction_user)
                                        if reaction_count["cancel"] == cancel_number_past:
                                            loop = False
                                            result = "cancel"
                                        else:
                                            pass
                                    else:
                                        await client.remove_reaction(check_msg, target_reaction.reaction.emoji, target_reaction.user)
                        if result == "err": #タイムアウトエラー
                            await client.send_message(send_ch, err_content)
                        elif result == "cancel": #キャンセル
                            await client.send_message(send_ch, "BANをキャンセルしました。\n" + accept_count_content)
                        elif result == "done": #実行
                            await client.send_message(send_ch, "BANを1分後に実行します。\n実行前に緊急停止するときには「!stop」と書き込んでください。\n" + accept_count_content)
                            while True:
                                stop_msg = await client.wait_for_message(timeout=stop_time, content="!stop", channel=message.channel)
                                if ((stop_msg == None) or (stop_time <= 0)):
                                    await client.send_message(send_ch, "BANを実行します。\n" + accept_count_content)
                                    try:
                                        await force_ban(user_id=ban_user_id, server_id=master_server_id, delete_message_days=1)
                                        result_check = True
                                    except:
                                        result_check = False
                                    file_name = file_directory + "/ban_log.txt"
                                    with open(file_name, "a", encoding="utf-8") as f:
                                        f.write("BAN対象ユーザー\n")
                                        f.write("名前: " + ban_user.name + "\nID: " + ban_user_id + "\n\n")
                                        f.write("コマンド起動者: " + message.author.name + "\n")
                                        f.write("実行者: " + done_user + "\n")
                                        f.write("拒否者: " + cancel_user + "\n")
                                    if result_check:
                                        result_content = "BANが完了しました。\n" + accept_count_content
                                    else:
                                        result_content = "BANに失敗しました。\n" + accept_count_content
                                    await client.send_message(send_ch, result_content)
                                    break
                                else: # "!stop"だ！
                                    result = "emergency_stop"
                                    await client.send_message(send_ch, "すべての処理を強制終了します。\n" + accept_count_content)
                                    break
                        else:
                            pass
                        # リアクションログを保存する。
                        file_name = file_directory + "/reaction_log.txt"
                        with open(file_name, "a", encoding="utf-8") as f:
                            f.write("最終的アクション: " + result + "\n\n")
                            for rc in ["done", "cancel"]:
                                f.write(rc + "ボタン\n\n")
                                for r in result_dict[rc]:
                                    f.write("時間: " + r["time"] + "\n")
                                    f.write("追加者: " + r["add_user"] + "\n")
                                    f.write("削除者: " + r["remove_user"] + "\n")
                                    f.write("カウント:" + r["count"] + "\n")
                                    f.write("-----------------\n")
                                f.write("\n")
                    else: # コマンド投稿者がその鯖でBAN権限を持っていなかった。
                        await client.send_message(send_ch, "連絡室のメンバーをBANすることはできません。")
                else:
                    await client.send_message(send_ch, err_content)
            else:
                await client.send_message(send_ch, err_content)
        else:
            pass

client.run("Token")
