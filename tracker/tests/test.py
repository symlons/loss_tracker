import unittest
from tracker import log
from tracker.manage_envs import Config

class TestLogClass(unittest.TestCase):

    def setUp(self):
        self.log = log()

    def test_initialization(self):
        self.assertEqual(self.log.name, "first")
        self.assertEqual(self.log.block_size, 2)
        self.assertEqual(self.log.x_list, [0])
        self.assertEqual(self.log.y_list, [])
        self.assertEqual(self.log.x_count, 0)

    def test_custom_initialization(self):
        custom_log = log(name="custom", block_size=5)
        self.assertEqual(custom_log.name, "custom")
        self.assertEqual(custom_log.block_size, 5)

    def test_push_single_value(self):
        self.log.push(1)
        self.assertEqual(self.log.y_list, [1])
        self.assertEqual(self.log.x_list, [0, 0])
        self.assertEqual(self.log.x_count, 1)

    def test_push_multiple_single_values(self):
        self.log.push(1)
        self.log.push(2)
        # After pushing 2 values, lists should be empty due to API call
        self.assertEqual(self.log.y_list, [])
        self.assertEqual(self.log.x_list, [])
        self.assertEqual(self.log.x_count, 2)

    def test_push_iterable(self):
        self.log.push([1, 2, 3])
        self.assertEqual(self.log.y_list, [1, 2, 3])
        self.assertEqual(self.log.x_list, [0, 1, 2])

    def test_block_size_behavior(self):
        self.log.push(1)
        self.assertEqual(len(self.log.y_list), 1)
        self.log.push(2)
        # After pushing 2 values, lists should be empty due to API call
        self.assertEqual(self.log.y_list, [])
        self.assertEqual(self.log.x_list, [])

    def test_zero_track(self):
        self.log.push([1, 2, 3])
        self.log.zero_track()
        self.assertEqual(self.log.x_list, [0])
        self.assertEqual(self.log.y_list, [])

    def test_push_empty_iterable(self):
        self.log.push([])
        self.assertEqual(self.log.y_list, [])
        self.assertEqual(self.log.x_list, [])

    def test_push_non_iterable(self):
        self.log.push(5)
        self.assertEqual(self.log.y_list, [5])
        self.assertEqual(self.log.x_list, [0, 0])
        self.assertEqual(self.log.x_count, 1)

    def test_large_block_size(self):
        large_block_log = log(block_size=1000)
        for i in range(999):
            large_block_log.push(i)
        self.assertEqual(len(large_block_log.y_list), 999)
        self.assertEqual(len(large_block_log.x_list), 1000)  # 999 + initial [0]
        large_block_log.push(999)
        # After pushing 1000 values, lists should be empty due to API call
        self.assertEqual(large_block_log.y_list, [])
        self.assertEqual(large_block_log.x_list, [])

if __name__ == '__main__':
    unittest.main()
