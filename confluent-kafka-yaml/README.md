This soon-to-be library came as a consequence of much boilerplate code that comes with
raw confluent-kafka library for python. I often find myself working on the same code 
over and over again. 

With this library, the entire communication with Kafka, including serialization for Producers
and deserialization for Consumers is reduced to a yaml config which is relatively easy to 
write and customize.

The sample format can be seen in $FENRIR_ROOT_DIR/confluent-kafka-yaml/app/config.yml.
This README will cover this topic in more detail within a few weeks.

~Lazar
