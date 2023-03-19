package ru.cib.springdatarest.entity

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.Id
import jakarta.persistence.ManyToOne
import jakarta.persistence.OneToMany
import jakarta.persistence.Table

@Entity
@Table(name = "_team")
data class TeamEntity(
    @Id
    @GeneratedValue
    var id: Int? = null,
    @Column(unique = true)
    var teamName: String? = null,
    var category: String? = null,
    @OneToMany
    var participants: MutableList<ParticipantEntity>? = null,
    @ManyToOne
    var hackathonEntity: HackathonEntity? = null
)
