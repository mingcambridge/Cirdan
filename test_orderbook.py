"""

This module contains the unit tests for process_orderbook python module.
it tests the OrderBook, getBestBidAndAsk and processOrder.

Usage:
    $ python test_orderbook.py

"""

import unittest
from orderbook import OrderBook
from orderbook import getBestBidAndAsk
from orderbook import processOrder

class TestOrderBook(unittest.TestCase):
    
    def test_1(self):
        ''' Test invalid order format.
        '''

        book = OrderBook()
        order = '1568390243|abbb11|a|AAPL|B|209.00000'
        result = processOrder(book, order)
        self.assertEqual(result, False, "Update should be failed with the wrong order format")

        order = '1568390243|abbb11|x'
        result = processOrder(book, order)
        self.assertEqual(result, False, "Update should be failed with the wrong action in order.")

        order = '1568390201|abbb11|a|AAPL|B|209.0000068|100'
        result = processOrder(book, order)
        self.assertEqual(result, False, "Update should be failed with the wrong price format in order.")

        order = '1568390201|abbb11|a|AAPL|B|209.0000068|-100'
        result = processOrder(book, order)
        self.assertEqual(result, False, "Update should be failed with the wrong size in order.")

    def test_2(self):
        ''' Test adding an order.
        '''

        book = OrderBook()
        order1 = '1568390243|abbb11|a|AAPL|B|209.00000|100'
        result = processOrder(book, order1)
        self.assertEqual(result, True, "The order should be correctly added")

        order = book.getOrder("abbb11")
        self.assertEqual(order.Ticker(), "AAPL", "The order ticker id should be AAPL.")

    def test_3(self):
        ''' Test the add action with the duplicate order id. 
        '''

        book = OrderBook()
        order1 = '1568390243|abbb11|a|AAPL|B|209.00000|100'
        result = processOrder(book, order1)
        self.assertEqual(result, True, "The order should be correctly added")

        order2 = '1568390243|abbb11|a|AAPL|B|209.00000|110'
        result = processOrder(book, order2)
        self.assertEqual(result, False, "Update should be failed with the duplicated order id for action add.")

    def test_4(self):
        ''' Test the update order.  
        '''

        book = OrderBook()
        order1 = '1568390243|abbb11|a|AAPL|B|209.00000|100'
        result = processOrder(book, order1)
        self.assertEqual(result, True, "The order should be correctly added")

        order2 = '1568390243|abbb11|u|110'
        result = processOrder(book, order2)
        self.assertEqual(result, True, "Order should be updated successfully.")

        order = book.getOrder("abbb11")
        self.assertEqual(order.Size(), 110, "The order size should be updated to 110.")

    def test_5(self):
        ''' Test the cancel order.  
        '''

        book = OrderBook()
        order1 = '1568390243|abbb11|a|AAPL|B|209.00000|100'
        result = processOrder(book, order1)
        self.assertEqual(result, True, "The order should be correctly added")

        order2 = '1568390243|abbb11|c'
        result = processOrder(book, order2)
        self.assertEqual(result,True, "Order should be cancelled successfully.")

        order = book.getOrder("abbb11")
        self.assertEqual(order, None, "There is no order with abbb11, as it has been cancelled.")

    def test_6(self):
        ''' Test Read mulitple orders from the file into the order book
            and get best bid and ask price for ticker
        '''
        book = OrderBook()
        with open("./testOrders.txt") as f:
            for order in f:
                processOrder(book, order)
        book.printOrderBook()
        ticker = 'AAPL'
        bid, ask = getBestBidAndAsk(book, ticker)
        
        self.assertEqual(bid, 210, "Best bid price Should be 210")
        self.assertEqual(ask, 202, "Best bid price Should be 202")

        
if __name__ == '__main__':
    unittest.main()


