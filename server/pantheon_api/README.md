Pantheon proto files can be found there: https://github.com/MahjongPantheon/pantheon/tree/master/Common

To install required tools: `asdf install`.

To install python lib: `pip install twirp`

To generate python code from proto files use 

1. `protoc --python_out=./ --twirpy_out=./ --plugin=protoc-gen-twirpy=./protoc-gen-twirpy ./frey.proto`
2. `protoc --python_out=./ --twirpy_out=./ --plugin=protoc-gen-twirpy=./protoc-gen-twirpy ./atoms.proto`
