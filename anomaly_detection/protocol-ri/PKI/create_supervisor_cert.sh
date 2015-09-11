export MPLANE_DIR=$(pwd)
export MPLANE_PKI_DIR=$MPLANE_DIR/ca

echo "
IMPORTANT: Before doing this, set the DNS name (SAN) and DN name you want for your supervisor, in etc/supervisor.conf 
"

echo "Enter certificate name: "
read name

echo "Creating TLS certificate request....."
openssl req -new -config $MPLANE_DIR/etc/supervisor.conf -out $MPLANE_PKI_DIR/certs/${name}.csr -keyout $MPLANE_PKI_DIR/certs/${name}.key

echo "Creating TLS certificate....."

openssl ca -config $MPLANE_DIR/etc/root-ca.conf -in $MPLANE_PKI_DIR/certs/${name}.csr -out $MPLANE_PKI_DIR/certs/${name}.crt -extensions server_ext

echo "Creating plaintext key....."

openssl pkey -in $MPLANE_PKI_DIR/certs/${name}.key -out $MPLANE_PKI_DIR/certs/${name}-plaintext.key

rm $MPLANE_PKI_DIR/certs/${name}.csr
