export MPLANE_DIR=$(pwd)
export MPLANE_PKI_DIR=$MPLANE_DIR/ca

echo "Creating CA directories..."

mkdir -p $MPLANE_PKI_DIR/root-ca/private $MPLANE_PKI_DIR/root-ca/db
chmod 700 $MPLANE_PKI_DIR/root-ca/private
mkdir -p $MPLANE_PKI_DIR/certs

#echo "Creating CA database...."

cp /dev/null $MPLANE_PKI_DIR/root-ca/db/root-ca.db
cp /dev/null $MPLANE_PKI_DIR/root-ca/db/root-ca.db.attr
echo 01 > $MPLANE_PKI_DIR/root-ca/db/root-ca.crt.srl
echo 01 > $MPLANE_PKI_DIR/root-ca/db/root-ca.crl.srl

echo "Creating CA request...."

openssl req -new -config $MPLANE_DIR/etc/root-ca.conf -out $MPLANE_PKI_DIR/root-ca/root-ca.csr -keyout $MPLANE_PKI_DIR/root-ca/private/root-ca.key

echo "Creating CA certificate...."

openssl ca -selfsign -config $MPLANE_DIR/etc/root-ca.conf -in $MPLANE_PKI_DIR/root-ca/root-ca.csr -out $MPLANE_PKI_DIR/root-ca/root-ca.crt -extensions root_ca_ext

rm $MPLANE_PKI_DIR/root-ca/*.pem $MPLANE_PKI_DIR/root-ca/*.csr

