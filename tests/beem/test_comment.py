from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from pprint import pprint
from beem import Steem, exceptions
from beem.comment import Comment, RecentReplies, RecentByPath
from beem.vote import Vote
from beem.instance import set_shared_steem_instance
from beem.utils import get_node_list

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=get_node_list(appbase=False),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        self.appbase = Steem(
            node=get_node_list(appbase=True),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_comment(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        with self.assertRaises(
            exceptions.ContentDoesNotExistsException
        ):
            Comment("@abcdef/abcdef", steem_instance=bts)
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        self.assertTrue(isinstance(c.id, int))
        self.assertTrue(c.id > 0)
        self.assertEqual(c.author, "gtg")
        self.assertEqual(c.permlink, "witness-gtg-log")
        self.assertEqual(c.authorperm, "@gtg/witness-gtg-log")
        self.assertEqual(c.category, 'witness-category')
        self.assertEqual(c.parent_author, '')
        self.assertEqual(c.parent_permlink, 'witness-category')
        self.assertEqual(c.title, 'witness gtg log')
        self.assertTrue(len(c.body) > 0)
        for key in ['tags', 'users', 'image', 'links', 'app', 'format']:
            self.assertIn(key, list(c.json_metadata.keys()))
        self.assertTrue(c.is_main_post())
        self.assertFalse(c.is_comment())
        self.assertTrue(isinstance(c.get_reblogged_by(), list))
        self.assertTrue(len(c.get_reblogged_by()) > 0)
        self.assertTrue(isinstance(c.get_votes(), list))
        if node_param == "appbase":
            self.assertTrue(len(c.get_votes()) > 0)
            self.assertTrue(isinstance(c.get_votes()[0], Vote))

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_vote(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.vote(100, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "vote"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["voter"])

        tx = c.upvote(weight=150, voter="test")
        op = tx["operations"][0][1]
        self.assertEqual(op["weight"], 10000)
        tx = c.downvote(weight=-150, voter="test")
        op = tx["operations"][0][1]
        self.assertEqual(op["weight"], -10000)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_export(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
            content = bts.rpc.get_content("gtg", "witness-gtg-log")
        else:
            bts = self.appbase
            content = bts.rpc.get_discussion({'author': 'gtg', 'permlink': 'witness-gtg-log'}, api="tags")

        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        keys = list(content.keys())
        json_content = c.json()

        for k in keys:
            if k not in "json_metadata" and k != 'reputation' and k != 'active_votes':
                self.assertEqual(content[k], json_content[k])

    def test_resteem(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.resteem(account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "custom_json"
        )

    def test_reply(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.reply(body="Good post!", author="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["author"])

    def test_delete(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.delete(account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "delete_comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["author"])

    def test_edit(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        c.edit(c.body, replace=False)
        body = c.body + "test"
        tx = c.edit(body, replace=False)
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["author"])

    def test_edit_replace(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        body = c.body + "test"
        tx = c.edit(body, meta=c["json_metadata"], replace=True)
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["author"])
        self.assertEqual(body, op["body"])

    def test_recent_replies(self):
        bts = self.bts
        r = RecentReplies("gtg", skip_own=True, steem_instance=bts)
        self.assertTrue(len(r) > 0)
        self.assertTrue(r[0] is not None)

    def test_recent_by_path(self):
        bts = self.bts
        r = RecentByPath(category="hot", steem_instance=bts)
        self.assertTrue(len(r) > 0)
        self.assertTrue(r[0] is not None)
