from tqdm import tqdm

from ..config import Endpoints as ep
from ..utils import ObjectGenerator as gen


# ====== USER ======


def get_user(self, user_id):
    resp = self._get(f'{ep.USER_v2}/{user_id}')
    user_data = resp['user']
    return gen.user_object(self, user_data)


def get_users_from_dict(self, resp):
    assert 'users' in resp, "'users' key not found"
    users_data = resp['users']
    users = []
    for user_data in users_data:
        user = gen.user_object(self, user_data)
        users.append(user)
    return users


def get_letters_from_dict(self, resp):
    assert 'reviews' in resp, "'reviews' key not found"
    reviews_data = resp['reviews']
    reviews = []
    for review_data in reviews_data:
        review = gen.review_object(self, review_data)
        reviews.append(review)
    return reviews


def get_letters(self, user_id, amount=None):
    # need a fix at next_item = resp.get('reviews')[-1]
    amount = float('inf') if amount is None else amount
    number = min(amount, 100)

    resp = self._get(
        f'{ep.USER_v1}/reviews/{user_id}?not_active=false&number={number}')
    reviews = self.get_letters_from_dict(resp)

    next_item = resp.get('reviews')[-1]
    next_id = next_item['id']
    reviews_count = self.get_user(user_id).reviews_count if amount == float(
        'inf') else amount
    amount -= 100

    with tqdm(total=reviews_count, desc='Extracting Letters') as pbar:
        while next_id and amount > 0:
            number = min(amount, 100)

            resp = self._get(
                f'{ep.USER_v1}/reviews/{user_id}?from_id={next_id}&not_active=false&number={number}')
            reviews.extend(self.get_letters_from_dict(resp))

            if len(resp['reviews']) == 0:
                break
            next_item = resp['reviews'][-1]
            next_id = next_item['id']
            amount -= 100

            pbar.update(number)

    return reviews


def get_joined_groups(self, user_id, amount=100):
    resp = self._get(
        f'{ep.GROUP_v1}/user_group_list?number={amount}&page=0&user_id={user_id}')
    return self.get_groups_from_dict(resp)


def get_user_followers(self, user_id, amount=None):
    amount = float('inf') if amount is None else amount
    number = min(amount, 50)

    resp = self._get(
        f'{ep.USER_v2}/{user_id}/web_followers?number={number}')
    users = self.get_users_from_dict(resp)

    next_id = resp.get('last_follow_id')
    followers_count = self.get_user(user_id).num_followers if amount == float(
        'inf') else amount
    amount -= 50

    with tqdm(total=followers_count, desc='Extracting Followers') as pbar:
        while next_id and amount > 0:
            number = min(amount, 50)

            resp = self._get(
                f'{ep.USER_v2}/{user_id}/web_followers?from_follow_id={next_id}&number={number}')
            users.extend(self.get_users_from_dict(resp))

            next_id = resp.get('last_follow_id')
            amount -= 50

            pbar.update(number)

    return users


def get_user_followings(self, user_id, amount=None):
    amount = float('inf') if amount is None else amount
    number = min(amount, 50)

    resp = self._get(
        f'{ep.USER_v2}/{user_id}/web_followings?number={number}')
    users = self.get_users_from_dict(resp)

    next_id = resp.get('last_follow_id')
    followings_count = self.get_user(user_id).num_followings if amount == float(
        'inf') else amount
    amount -= 50

    with tqdm(total=followings_count, desc='Extracting Followings') as pbar:
        while next_id and amount > 0:
            number = min(amount, 50)

            resp = self._get(
                f'{ep.USER_v2}/{user_id}/web_followings?from_follow_id={next_id}&number=50')
            users.extend(self.get_users_from_dict(resp))

            next_id = resp.get('last_follow_id')
            amount -= 50

            pbar.update(number)

    return users


def get_follow_requests(self, amount):
    # has last_timestamp: 1658812381
    resp = self._get(
        f'{ep.USER_v2}/follow_requests?number=50')
    return self.get_users_from_dict(resp)


def get_user_active_call(self, user_id):
    resp = self._get(
        f'{ep.POST_v1}/active_call?user_id={user_id}')
    post_id = resp['post'].get('id')
    return self.get_post(post_id)


def get_blocked_users(self, amount):
    resp = self._get(
        f'{ep.USER_v2}/blocked')
    return self.get_users_from_dict(resp)


# ====== POST ======


def get_post(self, post_id):
    resp = self._get(f'{ep.POST_v2}/{post_id}')
    post_data = resp.get('post')
    return gen.post_object(self, post_data)


def get_posts_from_dict(self, resp):
    assert 'posts' in resp, "'posts' key not found"
    posts_data = resp.get('posts')
    posts = []
    for post_data in posts_data:
        post = gen.post_object(self, post_data)
        posts.append(post)
    return posts


def get_timeline(self, user_id=None, keyword=None, hashtag=None, amount=100):
    if user_id:
        resp = self._get(
            f'{ep.GET_USER_TIMELINE}?number={amount}&user_id={user_id}')
    elif keyword:
        resp = self._get(
            f'{ep.GET_TIMELINE_BY_KEYWORD}?keyword={keyword}&number={amount}')
    elif hashtag:
        resp = self._get(
            f'{ep.GET_TIMELINE_BY_HASHTAG}/{hashtag}?number={amount}')
    else:
        resp = self._get(
            f'{ep.GET_TIMELINE}?number={amount}')
    return self.get_posts_from_dict(resp)


def get_following_timeline(self, amount=50):
    if amount > 50:
        pass
    # has next_page_value
    resp = self._get(
        f'{ep.GET_FOLLOWING_TIMELINE}?number=50')
    return self.get_posts_from_dict(resp)


def get_conversation(self, conversation_id=None, post_id=None, amount=100):
    if post_id:
        conversation_id = self.get_post(post_id).conversation_id
    resp = self._get(
        f'{ep.GET_CONVERSATION}/{conversation_id}?number={amount}&reverse=true')
    return self.get_posts_from_dict(resp)


def get_reposts(self, post_id, amount=100):
    resp = self._get(
        f'{ep.POST_v2}/{post_id}/reposts?number=100')
    return self.get_posts_from_dict(resp)


def get_post_likers(self, post_id, amount=50):
    # has last_id
    resp = self._get(
        f'{ep.POST_v1}/{post_id}/likers')
    return self.get_users_from_dict(resp)


# ====== GROUP ======


def get_group(self, group_id):
    resp = self._get(f'{ep.GROUP_v1}/{group_id}')
    group_data = resp.get('group')
    return gen.group_object(self, group_data)


def get_groups_from_dict(self, resp):
    assert 'groups' in resp, "'groups' key not found"
    groups_data = resp.get('groups')
    groups = []
    for group_data in groups_data:
        group = gen.group_object(self, group_data)
        groups.append(group)
    return groups


def get_group_users_from_dict(self, resp):
    assert 'group_users' in resp, "'group_users' key not found"
    users_data = resp.get('group_users')
    users = []
    for user_data in users_data:
        user = gen.group_user_object(self, user_data)
        users.append(user)
    return users


def get_group_timeline(self, group_id, amount=100):
    # {ep.POST_v2}/group_timeline?from_post_id=111&group_id={group_id}&number=100
    resp = self._get(
        f'{ep.POST_v2}/group_timeline?group_id={group_id}&number=100')
    return self.get_posts_from_dict(resp)


def get_group_call(self, group_id):
    resp = self._get(
        f'{ep.POST_v2}/call_timeline?group_id={group_id}&number=20')
    return self.get_posts_from_dict(resp)


def get_group_members(self, group_id, amount=100):
    resp = self._get(
        f'{ep.GROUP_v2}/{group_id}/members?number=100')
    return self.get_group_users_from_dict(resp)


def get_pending_users_in_group(self, group_id, amount=100):
    resp = self._get(
        f'{ep.GROUP_v2}/{group_id}/{group_id}/members?mode=pending&number=100')
    return self.get_users_from_dict(resp)


def get_banned_user_from_group(self, group_id, amount=100):
    resp = self._get(
        f'{ep.GROUP_v1}/{group_id}/{group_id}/ban_list?number=100')
    return self.get_users_from_dict(resp)


# ====== CHAT ======


def get_chat_room(self, chatroom_id):
    resp = self._get(f'{ep.CHATROOM_v2}/{chatroom_id}')
    chat_room_data = resp.get('chat')
    return gen.chat_room_object(chat_room_data)


def get_chat_rooms_from_dict(self, resp):
    assert 'chat_rooms' in resp, "'chat_rooms' key not found"
    chat_rooms_data = resp.get('chat_rooms')
    chats = []
    for chat_room_data in chat_rooms_data:
        chat = gen.chat_room_object(chat_room_data)
        chats.append(chat)
    return chats


def get_chat_messages_from_dict(self, resp):
    assert 'messages' in resp, "'messages' key not found"
    messages_data = resp.get('messages')
    messages = []
    for message_data in messages_data:
        message = gen.message_object(message_data)
        messages.append(message)
    return messages


def get_chat_room_id_from_user(self, user_id):
    data = {'with_user_id': user_id}
    resp = self._post(
        f'{ep.CHATROOM_v1}/new', data)
    return resp['room_id']


def get_chat_messages(self, chatroom_id=None, user_id=None, amount=None):
    resp = self._get(
        f'{ep.CHATROOM_v2}/{chatroom_id}/messages?number=100')
    return self.get_chat_messages_from_dict(resp)


def get_chat_rooms(self, amount=None):
    resp = self._get(
        f'{ep.CHATROOM_v1}/main_list?number=100')
    return self.get_chat_rooms_from_dict(resp)


def get_chat_requests(self, amount=None):
    resp = self._get(
        f'{ep.CHATROOM_v1}/request_list?number=100')
    return self.get_chat_rooms_from_dict(resp)


# ====== NOTIFICATION ======


def get_activities_from_dict(self, resp):
    assert 'activities' in resp, "'activities' key not found"
    activities_data = resp.get('activities')
    activities = []
    for activity_data in activities_data:
        activity = gen.activity_object(self, activity_data)
        activities.append(activity)
    return activities


def get_notification(self, important=True):
    if important:
        resp = self._get(
            f'{ep.CAS_BASE_URL}/api/user_activities?important=true&number=100')
    else:
        resp = self._get(
            f'{ep.CAS_BASE_URL}/api/user_activities?important=false&number=100')
    return self.get_activities_from_dict(resp)