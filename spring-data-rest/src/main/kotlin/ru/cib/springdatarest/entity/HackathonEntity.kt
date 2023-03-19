package ru.cib.springdatarest.entity

import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.Id
import jakarta.persistence.OneToMany
import jakarta.persistence.Table
import java.sql.Date

@Entity
@Table(name = "_hackathon")
data class HackathonEntity(
    @Id
    @GeneratedValue
    var id: Int? = null,
    var hackathonName: String? = null,
    var dateStart: Date? = null,
    var dateEnd: Date? = null,
    @OneToMany
    var teams: MutableList<TeamEntity>? = null
)
