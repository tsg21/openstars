# Minimal Firebase emulator image: just Node + a headless JRE (required by the
# Firestore emulator) + firebase-tools, with only the Firestore emulator jar
# downloaded. andreysenov/firebase-tools bundles the database/pubsub/storage
# emulators and build tooling we never use here, which makes it ~1.2GB.
#
# firebase-tools requires a JDK 21+ runtime, but Debian bookworm (node:22-slim's
# base) only ships OpenJDK 17, so the JRE is copied in from eclipse-temurin.
FROM eclipse-temurin:21-jre-jammy AS jre

FROM node:22-slim

COPY --from=jre /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

ARG FIREBASE_TOOLS_VERSION=15.25.1
RUN npm install -g firebase-tools@${FIREBASE_TOOLS_VERSION} \
    && npm cache clean --force

USER node
RUN firebase setup:emulators:firestore

WORKDIR /home/node
EXPOSE 4001 8085 9099

CMD ["firebase", "emulators:start", "--only", "auth,firestore"]
