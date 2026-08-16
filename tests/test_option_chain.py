from market_sentinel.providers.angelone.option_chain import OptionChain

chain = OptionChain()

nifty = chain.chain("NIFTY")

print("\nExpiries:", len(nifty))

for expiry, strikes in nifty.items():

    print(f"\n{expiry}")

    print("Total Strikes :", len(strikes))

    #
    # First 5 strikes
    #

    for strike, contracts in list(strikes.items())[:5]:

        print(
            strike,
            list(contracts.keys()),
        )