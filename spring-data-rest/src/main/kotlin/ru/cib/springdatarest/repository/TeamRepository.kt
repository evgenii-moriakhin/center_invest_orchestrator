package ru.cib.springdatarest.repository

import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.rest.core.annotation.RepositoryRestResource
import ru.cib.springdatarest.entity.TeamEntity

@RepositoryRestResource(collectionResourceRel = "team", path = "team")
interface TeamRepository : JpaRepository<TeamEntity, Int> {}