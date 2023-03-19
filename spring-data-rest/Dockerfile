FROM maven:3.8.4-openjdk-17-slim AS build

WORKDIR /app

COPY pom.xml .

COPY src /app/src

RUN mvn clean package -DskipTests

FROM openjdk:17-slim

WORKDIR /app

COPY --from=build /app/target/spring-data-rest-*.jar /app/spring-data-rest.jar

EXPOSE 8080

ENV SPRING_DATASOURCE_URL=jdbc:postgresql://your-remote-db-host:5432/hackathon2023
ENV SPRING_DATASOURCE_USERNAME=your-db-username
ENV SPRING_DATASOURCE_PASSWORD=your-db-password

CMD ["java", "-jar", "/app/spring-data-rest.jar"]
