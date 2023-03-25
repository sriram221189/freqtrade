# freqtrade

docker compose run freqtrade download-data --exchange binance -t 1h
docker-compose run freqtrade hyperopt --hyperopt-loss SharpeHyperOptLoss --strategy Supertrend -i 1h -e 1000 -j -1 --spaces buy roi stoploss trailing trades --timerange 20230310-20230322
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy Supertrend --timerange 20230220-20230321 -i 15m
docker-compose up -d
docker-compose logs -f
docker-compose down
