import datetime
import logging
import os
import random
import requests
import time

from ..config import Endpoints as ep
from ..exceptions import (
    YayError,
    AuthenticationError,
    ForbiddenError,
    RateLimitError,
    ExceedCallQuotaError,
    InvalidSignedInfo,
    UnknownError
)
from ..utils import handle_response, console_print
from .api_auth import YayAuth
from .api_chat import (
    send_message,
    accept_chat_request,
    delete_chat_room
)
from .api_get import (
    get_user,
    get_users_from_dict,
    get_hima_users,
    get_hima_users_from_dict,
    get_letters_from_dict,
    get_letters,
    get_joined_groups,
    get_user_followers,
    get_user_followings,
    get_follow_requests,
    get_user_active_call,
    get_blocked_users,
    get_post,
    get_posts_from_dict,
    get_timeline,
    get_following_timeline,
    get_conversation,
    get_reposts,
    get_post_likers,
    get_group,
    get_groups_from_dict,
    get_group_users_from_dict,
    get_group_timeline,
    get_group_call,
    get_group_members,
    get_pending_users_in_group,
    get_banned_user_from_group,
    get_chat_room,
    get_chat_rooms_from_dict,
    get_chat_messages_from_dict,
    get_chat_room_id_from_user,
    get_chat_messages,
    get_chat_rooms,
    get_chat_requests,
    get_activities_from_dict,
    get_notification,
)
from .api_group import (
    create_group,
    delete_group,
    change_group_settings,
    transfer_group_ownership,
    offer_group_sub_owner,
    undo_group_ownership_transfer,
    undo_group_sub_owner_offer,
    fire_group_sub_owner,
    accept_group_join_request,
    decline_group_join_request,
    invite_user_to_group,
    pin_group_post,
    unpin_group_post,
    ban_user_from_group,
    unban_user_from_group,
    join_group,
    leave_group,
)
from .api_post import (
    create_post,
    create_post_in_group,
    create_repost,
    create_reply,
    delete_post,
    pin_post,
    unpin_post,
    like_post,
    unlike_post,
)
from .api_user import (
    follow_user,
    unfollow_user,
    accept_follow_request,
    reject_follow_request,
    send_letter,
    block_user,
    unblock_user,
)

version = '0.3.3'  # also change .. __init__
current_path = os.path.abspath(os.getcwd())


class Yay(object):

    def __init__(
            self,
            token: str = None,
            proxy: str = None,
            timeout=10,
            base_path=current_path + '/config/',
            save_logfile=False,
            log_filename: str = None,
            loglevel_file=logging.DEBUG,
            loglevel_stream=logging.INFO,
    ):
        """

        YayBot
        ---
            Unofficial API for Yay! (yay.space) - developed by qualia-5w4

        """
        self.base_path = base_path

        # Setup logging
        self.logger = logging.getLogger('YayBot version: ' + version)

        if save_logfile is True:
            if not os.path.exists(base_path):
                # create base_path if not exists
                os.makedirs(base_path)

            if not os.path.exists(base_path + '/log/'):
                # create log folder if not exists
                os.makedirs(base_path + '/log/')

            if log_filename is None:
                log_filename = os.path.join(
                    base_path, 'log/yaybot_{}.log'.format(id(self))
                )

            fh = logging.FileHandler(filename=log_filename)
            fh.setLevel(loglevel_file)
            fh.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s (%(module)s %(pathname)s:%(lineno)s) - %(levelname)s - %(message)s'
                )
            )

            handler_existed = False
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler_existed = True
                    break
            if not handler_existed:
                self.logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(loglevel_stream)
        ch.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'))

        handler_existed = False
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler_existed = True
                break
        if not handler_existed:
            self.logger.addHandler(ch)
        self.logger.setLevel(logging.DEBUG)

        self.auth = YayAuth(proxy=proxy, timeout=timeout)

        if token:
            self.access_token = token
            self.auth.access_token = token
            self.auth.headers.setdefault('Authorization', f'Bearer {token}')

        self.logger.info('YayBot version: ' + version + ' Started!')

    def login(self, email, password):
        """
        ログインします。
        ---
            今後足跡が残ります。
        """
        self.auth.login(email, password)
        self.set_login_status()

    def logout(self):
        """
        ログアウトします。
        ---
            今後足跡は残りません。
        """
        self.auth.logout()
        self.pop_login_status()

    def set_login_status(self):
        self.access_token = self.auth.access_token
        self.refresh_token = self.auth.refresh_token
        self.expires_in = self.auth.expires_in
        self.api_key = self.auth.api_key
        self.logged_in_as = self.auth.logged_in_as

    def pop_login_status(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.api_key = None
        self.logged_in_as = None

    def _get(self, url: str):
        resp = requests.get(url, headers=self.auth.headers,
                            proxies=self.auth.proxies, timeout=self.auth.timeout)
        handle_response(resp)
        return resp.json()

    def _post(self, url: str, data: dict = None):
        resp = requests.post(url, params=data,
                             headers=self.auth.headers,
                             proxies=self.auth.proxies,
                             timeout=self.auth.timeout)
        handle_response(resp)
        return resp.json()

    def _put(self, url: str, data: dict = None):
        resp = requests.put(url, params=data,
                            headers=self.auth.headers,
                            proxies=self.auth.proxies,
                            timeout=self.auth.timeout)
        handle_response(resp)
        return resp.json()

    def _delete(self, url: str, data: dict = None):
        resp = requests.delete(url, params=data,
                               headers=self.auth.headers,
                               proxies=self.auth.proxies,
                               timeout=self.auth.timeout)
        handle_response(resp)
        return resp.json()

    # ====== GETTERS ======

    # user
    def get_user(self, user_id: str):
        """

        ユーザーの情報を取得します。

        Parameters:
            user_id (str): ユーザーのID

        Returns:
            User: ユーザーのオブジェクト

        Examples:
            ID '123'のユーザー名を取得する場合
        >>> get_user('123').screen_name

        """
        return get_user(self, user_id)

    def get_hima_users(self, amount: int = None):
        """

        暇なユーザーを取得します。

        Parameters:
            amount (int): 取得するユーザーの数 (任意、最大で約200～500人くらい)

        Returns:
            User: ユーザーのオブジェクト

        Examples:
            ID '123'のユーザー名を取得する場合
        >>> get_user('123').screen_name

        """
        return get_hima_users(self, amount)

    def get_users_from_dict(self, resp: dict):
        return get_users_from_dict(self, resp)

    def get_hima_users_from_dict(self, resp: dict):
        return get_hima_users_from_dict(self, resp)

    def get_letters_from_dict(self, resp: dict):
        return get_letters_from_dict(self, resp)

    def get_letters(self, user_id: str, amount: int = None):
        """

        ユーザーが受け取ったレターを取得します。

        Parameters:
            user_id (str): ユーザーのID
            amount (int): 取得するレターの数

        Returns:
            Letter (list): レターオブジェクトのリスト

        """
        return get_letters(self, user_id, amount)

    def get_joined_groups(self, user_id: str, amount=100):
        """

        ユーザーが参加しているグループを取得します。

        Parameters:
            user_id (str): ユーザーのID
            amount (int): 取得するグループの数

        Returns:
            Group (list): グループオブジェクトのリスト

        """
        return get_joined_groups(self, user_id, amount)

    def get_user_followers(self, user_id: str, amount: int = None):
        """

        ユーザーのフォロワーを取得します。

        Parameters:
            user_id (str): ユーザーのID
            amount (int): 取得するユーザーの数

        Returns:
            User (list): ユーザーオブジェクトのリスト

        """
        return get_user_followers(self, user_id, amount)

    def get_user_followings(self, user_id, amount=None):
        """

        ユーザーのフォロー中を取得します。

        Parameters:
            user_id (str): ユーザーのID
            amount (int): 取得するユーザーの数

        Returns:
            User (list): ユーザーオブジェクトのリスト

        """
        return get_user_followings(self, user_id, amount)

    def get_follow_requests(self, amount=100):
        """

        フォローリクエストのユーザーを取得します。

        Parameters:
            amount (int): 取得するユーザーの数

        Returns:
            User (list): ユーザーオブジェクトのリスト

        """
        return get_follow_requests(self, amount)

    def get_user_active_call(self, user_id: str):
        """

        ユーザーが参加している通話の情報を取得します。

        Parameters:
            user_id (str): ユーザーのID

        Returns:
            Post : 投稿オブジェクト

        Examples:
            ID '123'のユーザーが参加している通話の枠主の名前を取得する場合
        >>> get_user_active_call('123').author_screen_name

        """
        return get_user_active_call(self, user_id)

    def get_blocked_users(self, amount=100):
        """

        ブロックしているユーザーを取得します。

        Parameters:
            amount (int): 取得するユーザーの数

        Returns:
            User (list): ユーザーオブジェクトのリスト

        """
        return get_blocked_users(self, amount)

    # post
    def get_post(self, post_id: str):
        """

        投稿の情報を取得します。

        Parameters:
            post_id (str): 投稿のID

        Returns:
            Post : 投稿オブジェクト

        Examples:
            ID '123'の投稿本文を取得する場合
        >>> get_post('123').text

        """
        return get_post(self, post_id)

    def get_posts_from_dict(self, resp: dict):
        return get_posts_from_dict(self, resp)

    def get_timeline(self, user_id: str = None, keyword: str = None, hashtag: str = None, amount=100):
        """

        タイムラインの投稿を取得します。

        Parameters:
            user_id (str): ユーザーID (特定のユーザーのタイムラインを取得する場合)
            keyword (str): キーワード (特定の単語が含まれている投稿を取得する場合)
            hashtag (str): ハッシュタグ (特定のタグが含まれている投稿を取得する場合)
            amount (int): 取得する投稿の数

        Returns:
            Post (list): 投稿オブジェクトのリスト

        """
        return get_timeline(self, user_id, keyword, hashtag, amount)

    def get_following_timeline(self, amount=50):
        """

        フォロー中のタイムラインの投稿を取得します。

        Parameters:
            amount (int): 取得する投稿の数

        Returns:
            Post (list): 投稿オブジェクトのリスト

        """
        return get_following_timeline(self, amount)

    def get_conversation(self, conversation_id: str = None, post_id: str = None, amount=100):
        """

        会話の投稿を取得します。

        Parameters:
            conversation_id (str): 会話のID (post_idを指定する場合は任意)
            post_id (str): 投稿のID (conversation_idを指定する場合は任意)
            amount (int): 取得する投稿の数

        Returns:
            Post (list): 投稿オブジェクトのリスト

        """
        return get_conversation(self, conversation_id, post_id, amount)

    def get_reposts(self, post_id, amount=100):
        """

        投稿の(´∀｀∩)↑age↑を取得します。

        Parameters:
            post_id (str): 投稿のID
            amount (int): 取得する投稿の数

        Returns:
            Post (list): 投稿オブジェクトのリスト

        """
        return get_reposts(self, post_id, amount)

    def get_post_likers(self, post_id, amount: int = None):
        """

        投稿にいいねしたユーザーを取得します。

        Parameters:
            post_id (str): 投稿のID
            amount (int): 取得する投稿の数 (任意)

        Returns:
            User (list): ユーザーオブジェクトのリスト

        """
        return get_post_likers(self, post_id, amount)

    # group
    def get_group(self, group_id: str):
        """

        IDで指定したサークルの情報を取得します。

        Parameters:
            group_id (str): サークルのID

        Returns:
            Group: グループオブジェクト

        Examples:
            ID '123'のサークルの説明欄を取得する場合
        >>> get_group('123').description

        """
        return get_group(self, group_id)

    def get_groups_from_dict(self, resp: dict):
        return get_groups_from_dict(self, resp)

    def get_group_users_from_dict(self, resp: dict):
        return get_group_users_from_dict(self, resp)

    def get_group_timeline(self, group_id: str, amount=100):
        """

        IDで指定したサークルの投稿を取得します。

        Parameters:
            group_id (str): サークルのID
            amount (int): 投稿の数

        Returns:
            Post (list): 投稿オブジェクトのリスト

        """
        return get_group_timeline(self, group_id, amount)

    def get_group_call(self, group_id: str):
        """

        IDで指定したサークルの通話中の投稿を取得します。

        Parameters:
            group_id (str): サークルのID

        Returns:
            Post (list): 投稿オブジェクトのリスト

        """
        return get_group_call(self, group_id)

    def get_group_members(self, group_id: str, amount=100):
        """

        IDで指定したサークルのメンバーを取得します。

        Parameters:
            group_id (str): サークルのID
            amount (int): メンバー数 (省略可)

        Returns:
            GroupUser (list): グループメンバーオブジェクトのリスト

        Examples:
            ID '123'のサークルのメンバー50人を取得する場合
        >>> get_group_members('123', 50)

        """
        return get_group_members(self, group_id, amount)

    def get_pending_users_in_group(self, group_id: str, amount=100):
        """

        IDで指定したサークルの参加リクエスト保留中のユーザーを取得します。

        Parameters:
            group_id (str): サークルのID
            amount (int): ユーザー数 (省略可)

        Returns:
            GroupUser (list): グループメンバーオブジェクトのリスト

        Examples:
            ID '123'のサークルの参加リクエスト保留中のユーザーを取得する場合
        >>> get_pending_users_in_group('123')

        """
        return get_pending_users_in_group(self, group_id, amount)

    def get_banned_user_from_group(self, group_id: str, amount=100):
        """

        IDで指定したサークルから追放されたユーザーを取得します。

        Parameters:
            group_id (str): サークルのID
            amount (int): ユーザー数 (省略可)

        Returns:
            GroupUser (list): グループメンバーオブジェクトのリスト

        """
        return get_banned_user_from_group(self, group_id, amount)

    # chat
    def get_chat_room(self, chatroom_id: str):
        """

        IDで指定したチャットルームの情報を取得します。

        Parameters:
            chatroom_id (str): チャットルームのID

        Returns:
            ChatRoom: チャットルームオブジェクト

        Examples:
            ID '123'のチャットルームのメンバーのIDを取得する場合
        >>> get_chat_room('123').member_ids

        """
        return get_chat_room(self, chatroom_id)

    def get_chat_rooms_from_dict(self, resp: dict):
        return get_chat_rooms_from_dict(self, resp)

    def get_chat_messages_from_dict(self, resp: dict):
        return get_chat_messages_from_dict(self, resp)

    def get_chat_room_id_from_user(self, user_id: str):
        """

        ユーザーIDからチャットを開始するためのIDを取得します。

        Parameters:
            user_id (str): ユーザーのID

        Returns:
            room_id (str): チャットルームのID

        Examples:
            ID '123'のユーザーとのチャットルームIDを取得する場合
        >>> get_chat_room_id_from_user('123')

        """
        return get_chat_room_id_from_user(self, user_id)

    def get_chat_messages(self, chatroom_id: str = None, user_id: str = None, amount: int = None):
        """

        IDで指定したチャットルーム、\n
        もしくはユーザーIDからチャットメッセージを取得します。

        Parameters:
            chatroom_id (str): チャットルームのID (user_idを指定する場合は任意)
            user_id (str): ユーザーID (chatroom_idを指定する場合は任意)

        Returns:
            Message (list): メッセージオブジェクトのリスト

        Examples:
            ID '123'のユーザーとのチャットを取得する場合
        >>> get_chat_messages(user_id='123')

        """
        return get_chat_messages(self, chatroom_id, user_id, amount)

    def get_chat_rooms(self, amount: int = None):
        """

        チャットルームを取得します。

        Parameters:
            amount (int): チャットルームの数

        Returns:
            ChatRoom (list): チャットルームオブジェクトのリスト

        """
        return get_chat_rooms(self, amount)

    def get_chat_requests(self, amount: int = None):
        """

        あなた宛の保留中のチャットリクエストを取得します。

        Parameters:
            amount (int): チャットルームの数

        Returns:
            ChatRoom (list): チャットルームオブジェクトのリスト

        """
        return get_chat_requests(self, amount)

    # notification
    def get_activities_from_dict(self, resp: dict):
        return get_activities_from_dict(self, resp)

    def get_notification(self, important=True, amount=100):
        """

        通知を取得します。

        Parameters:
            important (bool): Trueにすると重要な通知を取得します。

        Returns:
            Activity (list): 通知オブジェクトのリスト

        """
        return get_notification(self, important)

    # ====== USER ======

    def follow_user(self, user_id: str) -> dict:
        """

        IDで指定したユーザーをフォローします。

        Parameters:
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'のユーザーをフォローする場合
        >>> follow_user(user_id='123')

        """
        return follow_user(self, user_id)

    def unfollow_user(self, user_id: str) -> dict:
        """

        IDで指定したユーザーのフォローを解除します。

        Parameters:
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> unfollow_user(user_id='123')

        """
        return unfollow_user(self, user_id)

    def accept_follow_request(self, user_id: str) -> dict:
        """

        IDで指定したユーザーからのフォローリクエストを承認します。

        Parameters:
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> accept_follow_request(user_id='123')

        """
        return accept_follow_request(self, user_id)

    def reject_follow_request(self, user_id: str) -> dict:
        """

        IDで指定したユーザーからのフォローリクエスト拒否します。

        Parameters:
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> reject_follow_request(user_id='123')

        """
        return reject_follow_request(self, user_id)

    def send_letter(self, user_id: str, message: str) -> dict:
        """

        IDで指定したユーザーにレターを送信します。

        Parameters:
            user_id (str): ユーザーID
            message (str): レター本文

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> send_letter(user_id='123', message='こんにちは')

        """
        return send_letter(self, user_id, message)

    def block_user(self, user_id: str) -> dict:
        """

        IDで指定したユーザーをブロックします。

        Parameters:
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> block_user(user_id='123')

        """
        return block_user(self, user_id)

    def unblock_user(self, user_id: str) -> dict:
        """

        IDで指定したユーザーのブロックを解除します。

        Parameters:
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> unblock_user(user_id='123')

        """
        return unblock_user(self, user_id)

    # ====== POST ======

    def create_post(self, text: str, color=0, font_size=0, choices: list = None) -> dict:
        """

        投稿します。

        Parameters:
            text (str): 投稿本文
            color (int): 文字色
            font_size (int): 文字の大きさ
            choices (list): アンケートの選択肢

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> create_post(text='こんにちは' color=2)

        文字色の種類:

            普通の色: 0 から 7
            特殊な色: 1001 から 1007

        文字の大きさ:

            0 から 4 (文字の大きさは数値の大きさに比例します)

        アンケート:

            choices引数に選択肢として文字列リストを渡してください。

        """
        return create_post(self, text, color, font_size, choices)

    def create_post_in_group(self, group_id: str, text: str, color=0, font_size=0, choices: list = None, type: str = None) -> dict:
        """

        IDで指定したグループで投稿します。

        Parameters:
            text (str): 投稿本文
            color (int): 文字色
            font_size (int): 文字の大きさ
            choices (list): アンケートの選択肢
            type (str): 投稿の種類

        Returns:
            Result (dict): 実行結果

        Examples:
        >>> create_post(text='こんにちは' color=2)

        文字色の種類:

            普通の色: 0 から 7
            特殊な色: 1001 から 1007

        文字の大きさ:

            0 から 4 (文字の大きさは数値の大きさに比例します)

        """
        return create_post_in_group(self, group_id, text, color, font_size, choices, type)

    def create_repost(self, text: str, post_id: str, color=0, font_size=0) -> dict:
        """

        IDで指定した投稿を(´∀｀∩)↑age↑します。

        Parameters:
            text (str): 投稿本文
            user_id (str): ユーザーID
            font_size (int): 文字の大きさ

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿を(´∀｀∩)↑age↑する場合
        >>> create_repost(text='すごい', post_id='123')

        文字色の種類:

            普通の色: 0 から 7
            特殊な色: 1001 から 1007

        文字の大きさ:

            0 から 4 (文字の大きさは数値の大きさに比例します)

        """
        return create_repost(self, text, post_id, color, font_size)

    def create_reply(self, text: str, post_id: str, color=0, font_size=0) -> dict:
        """

        IDで指定した投稿に返信します。

        Parameters:
            text (str): 投稿本文
            user_id (str): ユーザーID
            font_size (int): 文字の大きさ

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿に返信する場合
        >>> create_reply(text='すごい', post_id='123')

        文字色の種類:

            普通の色: 0 から 7
            特殊な色: 1001 から 1007

        文字の大きさ:

            0 から 4 (文字の大きさは数値の大きさに比例します)

        """
        return create_reply(self, text, post_id, color, font_size)

    def delete_post(self, post_id: str) -> dict:
        """

        IDで指定した投稿を削除します。

        Parameters:
            post_id (str): 投稿のID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿を削除する場合
        >>> delete_post(post_id='123')

        """
        return delete_post(self, post_id)

    def pin_post(self, post_id: str) -> dict:
        """

        IDで指定した投稿をプロフィールにピンします。

        Parameters:
            post_id (str): 投稿のID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿をピンする場合
        >>> pin_post(post_id='123')

        """
        return pin_post(self, post_id)

    def unpin_post(self, post_id: str) -> dict:
        """

        IDで指定したピン投稿のピンを解除します。

        Parameters:
            post_id (str): 投稿のID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿のピンを解除する場合
        >>> unpin_post(post_id='123')

        """
        return unpin_post(self, post_id)

    def like_post(self, post_id: str) -> dict:
        """

        IDで指定した投稿をいいねします。

        Parameters:
            post_id (str): 投稿のID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿をいいねする場合
        >>> like_post(post_id='123')

        """
        return like_post(self, post_id)

    def unlike_post(self, post_id: str) -> dict:
        """

        IDで指定した投稿のいいねを取り消します。

        Parameters:
            post_id (str): 投稿のID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'の投稿のいいねを取り消す場合
        >>> unlike_post(post_id='123')

        """
        return unlike_post(self, post_id)

    # ====== GROUP ======

    def create_group(
        self,
        group_name: str,
        description: str = None,
        guidelines: str = None,
        group_category_id=21,
        sub_category_id: int = None,
        is_private=None,
        call_timeline_display=True,
        hide_reported_posts=False,
        allow_ownership_transfer=True,
        allow_thread_creation_by='member',
        allow_members_to_post_image_and_video=True,
        allow_members_to_post_url=True,
        hide_conference_call=False,
        secret=False,
        only_verified_age=False,
        only_mobile_verified=False,
        gender=-1,
        generation_groups_limit=0
    ) -> dict:
        """

        サークルを作成します。

        Parameters:

            group_name (str): サークル名

            description (str): 説明欄

            guidelines (str): 規約欄

            group_category_id (int): ジャンル

            sub_category_id (int): サブジャンル

            is_private (bool): 承認制

            call_timeline_display (bool): 通話をトップに表示

            hide_reported_posts (bool): 不適切な投稿を非表示

            allow_ownership_transfer (bool): 管理人権限の引き継ぎを許可

            allow_thread_creation_by (str): スレッドを作成可能なメンバー 例) 'member'

            allow_members_to_post_image_and_video (bool): 誰でも画像と動画を投稿可能

            allow_members_to_post_url (bool): 誰でもURLを投稿可能

            hide_conference_call (bool): サークルカテゴリーの一覧に非表示

            secret (bool): 検索結果に非表示

            only_verified_age (bool): 年齢確認必須

            only_mobile_verified (bool): 電話番号認証必須

            gender (int): 参加できる性別を限定

            generation_groups_limit (int): 18歳以上のみに限定

        Returns:
            Result (dict): 実行結果

        """
        return create_group(
            self,
            group_name,
            description,
            guidelines,
            group_category_id,
            sub_category_id,
            is_private,
            call_timeline_display,
            hide_reported_posts,
            allow_ownership_transfer,
            allow_thread_creation_by,
            allow_members_to_post_image_and_video,
            allow_members_to_post_url,
            hide_conference_call,
            secret,
            only_verified_age,
            only_mobile_verified,
            gender,
            generation_groups_limit
        )

    def delete_group(self, group_id: str) -> dict:
        """

        IDで指定したサークルを削除します。(管理人限定)

        Parameters:
            group_id (str): グループID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'のグループを削除する場合
        >>> delete_group(group_id='123')

        """
        return delete_group(self, group_id)

    def change_group_settings(
        self,
        group_id,
        group_name: str = None,
        description: str = None,
        guidelines: str = None,
        group_category_id=21,
        sub_category_id: int = None,
        is_private=None,
        call_timeline_display=True,
        hide_reported_posts=False,
        allow_ownership_transfer=True,
        allow_thread_creation_by='member',
        allow_members_to_post_image_and_video=True,
        allow_members_to_post_url=True,
        hide_conference_call=False,
        hide_from_game_eight=False,
        secret=False,
        only_verified_age=False,
        only_mobile_verified=False,
        gender=-1,
        generation_groups_limit=0
    ) -> dict:
        """

        サークルの設定を変更します。

        Parameters:

            group_name (str): サークル名

            description (str): 説明欄

            guidelines (str): 規約欄

            group_category_id (int): ジャンル

            sub_category_id (int): サブジャンル

            is_private (bool): 承認制

            call_timeline_display (bool): 通話をトップに表示

            hide_reported_posts (bool): 不適切な投稿を非表示

            allow_ownership_transfer (bool): 管理人権限の引き継ぎを許可

            allow_thread_creation_by (str): スレッドを作成可能なメンバー 例) 'member'

            allow_members_to_post_image_and_video (bool): 誰でも画像と動画を投稿可能

            allow_members_to_post_url (bool): 誰でもURLを投稿可能

            hide_conference_call (bool): サークルカテゴリーの一覧に非表示

            secret (bool): 検索結果に非表示

            only_verified_age (bool): 年齢確認必須

            only_mobile_verified (bool): 電話番号認証必須

            gender (int): 参加できる性別を限定

            generation_groups_limit (int): 18歳以上のみに限定

        Returns:
            Result (dict): 実行結果

        """
        return change_group_settings(
            self,
            group_id,
            group_name,
            description,
            guidelines,
            group_category_id,
            sub_category_id,
            is_private,
            call_timeline_display,
            hide_reported_posts,
            allow_ownership_transfer,
            allow_thread_creation_by,
            allow_members_to_post_image_and_video,
            allow_members_to_post_url,
            hide_conference_call,
            hide_from_game_eight,
            secret,
            only_verified_age,
            only_mobile_verified,
            gender,
            generation_groups_limit
        )

    def transfer_group_ownership(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーに管理人権限の引き継ぎをオファーします。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return transfer_group_ownership(self, group_id, user_id)

    def offer_group_sub_owner(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーに副管理人の権限をオファーします。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return offer_group_sub_owner(self, group_id, user_id)

    def undo_group_ownership_transfer(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーの管理人権限の引き継ぎオファーを取り消します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return undo_group_ownership_transfer(self, group_id, user_id)

    def undo_group_sub_owner_offer(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーの副管理人の権限オファーを取り消します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return undo_group_sub_owner_offer(self, group_id, user_id)

    def fire_group_sub_owner(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定した副管理人をクビにします。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return fire_group_sub_owner(self, group_id, user_id)

    def accept_group_join_request(self, group_id: str, user_id: str) -> dict:
        """

        サークルへの参加リクエストを許可します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return accept_group_join_request(self, group_id, user_id)

    def decline_group_join_request(self, group_id: str, user_id: str) -> dict:
        """

        サークルへの参加リクエストを拒否します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return decline_group_join_request(self, group_id, user_id)

    def invite_user_to_group(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーサークルに招待します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'のユーザーをID '456'のサークルに招待する場合
        >>> invite_user_to_group(user_id='123', group_id='456')

        """
        return invite_user_to_group(self, group_id, user_id)

    def pin_group_post(self, group_id: str, post_id: str) -> dict:
        """

        IDで指定したグループの投稿をピンします。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        """
        return pin_group_post(self, group_id, post_id)

    def unpin_group_post(self, group_id: str) -> dict:
        """

        IDで指定したグループのピン投稿を解除します。

        Parameters:
            group_id (str): グループID

        Returns:
            Result (dict): 実行結果

        """
        return unpin_group_post(self, group_id)

    def ban_user_from_group(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーをサークルから追放します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '123'のユーザーを ID '456'のサークルから追放する場合
        >>> ban_user_from_group(user_id='123', group_id='456')

        """
        return ban_user_from_group(self, group_id, user_id)

    def unban_user_from_group(self, group_id: str, user_id: str) -> dict:
        """

        IDで指定したユーザーの追放を解除します。

        Parameters:
            group_id (str): グループID
            user_id (str): ユーザーID

        Returns:
            Result (dict): 実行結果

        Examples:
            ID '456'のサークルから追放された ID '123'の追放されたユーザーを解除する場合
        >>> ban_user_from_group(user_id='123', group_id='456')

        """
        return unban_user_from_group(self, group_id, user_id)

    def join_group(self, group_id: str) -> dict:
        """

        IDで指定したサークルに参加します。

        Parameters:
            group_id (str): グループID

        Returns:
            Result (dict): 実行結果

        """
        return join_group(self, group_id)

    def leave_group(self, group_id: str) -> dict:
        """

        IDで指定したサークルから脱退します。

        Parameters:
            group_id (str): グループID

        Returns:
            Result (dict): 実行結果

        """
        return leave_group(self, group_id)

    # ====== CHAT ======

    def send_message(self, message: str, user_id: str = None, chat_room_id: str = None) -> dict:
        """

        IDで指定したユーザー、\n
        もしくはチャットルームにメッセージを送信します。


        Parameters:
            message (str): メッセージ本文
            user_id (str): ユーザーのID (chat_room_idを指定する場合は任意)
            chat_room_id (str): チャットルームのID (user_idを指定する場合は任意)

        Returns:
            Result (dict): 実行結果

        """
        return send_message(self, message, user_id, chat_room_id)

    def accept_chat_request(self, chat_room_id: str) -> dict:
        """

        IDで指定したチャットリクエストを承認します。

        Parameters:
            chat_room_id (str): チャットルームのID

        Returns:
            Result (dict): 実行結果

        """
        return accept_chat_request(self, chat_room_id)

    def delete_chat_room(self, chat_room_id: str) -> dict:
        """

        IDで指定したチャットルームを削除します。

        Parameters:
            chat_room_id (str): チャットルームのID

        Returns:
            Result (dict): 実行結果

        """
        return delete_chat_room(self, chat_room_id)

    # ====== SUPPORT ======

    def console_print(self, text: str, color: str = None) -> None:
        return console_print(text, color)
