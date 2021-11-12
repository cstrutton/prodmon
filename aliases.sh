build() {
  docker build -t prodmon-$1 --file prodmon-$1.dockerfile .
}

run() {
  docker run -d \
  --restart=unless-stopped \
  --volume sql:/code/tempSQL \
  --name $1 \
  prodmon-$1 $2
}

stop() {
  docker stop $1
  docker rm $1
}

update() {
  stop collect
  stop post
  git pull
  build collect
  build post
}