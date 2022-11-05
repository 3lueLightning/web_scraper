# for linux
#sed -i 's/cdc_/did_/g' chromedriver_mac64_10605249_mod

# https://singhkays.com/blog/sed-error-i-expects-followed-by-text/
LC_ALL=C sed -i'.bak' -e 's|cdc_|did_|g' chromedriver_mac64_10605249_mod

# cd /usr/local/bin/
# cp chromedriver chromedriver_bkp
# LC_ALL=C sed -i'.bak' -e 's|cdc_|did_|g' chromedriver