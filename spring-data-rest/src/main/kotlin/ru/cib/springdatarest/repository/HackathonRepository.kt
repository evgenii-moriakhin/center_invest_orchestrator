package ru.cib.springdatarest.repository

import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.rest.core.annotation.RepositoryRestResource
import ru.cib.springdatarest.entity.HackathonEntity

@RepositoryRestResource(collectionResourceRel = "hackathon", path = "hackathon")
interface HackathonRepository : JpaRepository<HackathonEntity, Int> {}