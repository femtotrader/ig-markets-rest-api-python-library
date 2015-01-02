IG Markets REST API - Python Library
------------------------------------

A lightweight Python library that can be used to connect to the IG
Markets REST API with a LIVE or DEMO account.

You can use the IG Markets HTTP / REST API to submit trade orders, open
positions, close positions and view market sentiment. IG Markets provide
Retail Spread Betting and CFD accounts for trading Equities, Forex,
Commodities, Indices and much more.

Full details about the API along with information about how to open an
account with IG can be found at the link below:

http://labs.ig.com/

How To Use The Library
----------------------

Using this library to connect to the IG Markets API is extremely easy.
All you need to do is import the IGService class, create an instance,
and call the methods you wish to use. There is a method for each
endpoint exposed by their API. The code sample below shows you how to
connect to the API, switch to a secondary account and retrieve all open
positions for the active account.

**Note:** The secure session with IG is established when you create an
instance of the IGService class.

.. code:: python

    from ig_service import IGService
    from ig_service_config import *

    ig_service = IGService(username, password, api_key, acc_type)
    ig_service.create_session()

    account_info = ig_service.switch_account(acc_number, False)
    print(account_info)

    open_positions = ig_service.fetch_open_positions()
    print("open_positions:\n%s" % open_positions)

    print("")

    epic = 'CS.D.EURUSD.MINI.IP'
    resolution = 'DAY'
    num_points = 10
    response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points)
    df_ask = response['prices']['price']['ask']
    print("ask prices:\n%s" % df_ask)

with ``ig_service_config.py``

.. code:: python

    username = "YOUR_USERNAME"
    password = "YOUR_PASSWORD"
    api_key = "YOUR_API_KEY"
    acc_type = "DEMO" # LIVE / DEMO
    acc_number = "ABC123"

it should display:

::

    open_positions:
    Empty DataFrame
    Columns: []
    Index: []

    ask prices:
                            Open     High      Low    Close
    DateTime
    2014:11:18-00:00:00  1.24510  1.25465  1.24442  1.25330
    2014:11:19-00:00:00  1.25332  1.26013  1.25127  1.25461
    2014:11:20-00:00:00  1.25463  1.25760  1.25048  1.25427
    2014:11:21-00:00:00  1.25428  1.25689  1.23755  1.23924
    2014:11:23-00:00:00  1.23640  1.23770  1.23607  1.23725
    2014:11:24-00:00:00  1.23864  1.24453  1.23830  1.24390
    2014:11:25-00:00:00  1.24389  1.24877  1.24026  1.24743
    2014:11:26-00:00:00  1.24744  1.25322  1.24443  1.25077
    2014:11:27-00:00:00  1.25078  1.25244  1.24569  1.24599
    2014:11:28-00:00:00  1.24598  1.24909  1.24269  1.24505

Many IGService methods return `Python
Pandas <http://pandas.pydata.org/>`__ DataFrame, Series or Panel.
