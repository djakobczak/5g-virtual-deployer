set -u

while true; do
	if grep "Connection refused" /tmp/connect-core-1ue.log -q; then
		if grep "SCTP connection established" /tmp/connect-core-1ue-restart.log -q; then
			echo established
			exit 0
		fi
  		echo "refused"
  		sudo pkill -f "sudo bash -c scripts/bootstrap_gnb.sh"
		sudo pkill -f "nr-gnb"
		ps aux | grep gnb
		sleep 0.4
		./scripts/bootstrap_gnb.sh &
	fi
	sleep 0.1
done
