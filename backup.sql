-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: plant_bot
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `plant_notes`
--

DROP TABLE IF EXISTS `plant_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plant_notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plant_id` int NOT NULL,
  `date` date NOT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `plant_id` (`plant_id`),
  CONSTRAINT `plant_notes_ibfk_1` FOREIGN KEY (`plant_id`) REFERENCES `plants` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plant_notes`
--

LOCK TABLES `plant_notes` WRITE;
/*!40000 ALTER TABLE `plant_notes` DISABLE KEYS */;
INSERT INTO `plant_notes` VALUES (1,2,'2025-10-31','Я родился'),(2,2,'2025-01-11','я расту'),(3,2,'2025-01-11','Произведена обрезка'),(4,9,'2025-10-10','Купание'),(5,9,'2025-10-15','Обработка органическими удобрениями'),(6,9,'2025-10-23','Обрезка'),(7,11,'2025-11-01','Полив');
/*!40000 ALTER TABLE `plant_notes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `plants`
--

DROP TABLE IF EXISTS `plants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `height` decimal(5,2) DEFAULT NULL,
  `soil` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `light` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `watering_interval` int DEFAULT NULL,
  `last_watered` date DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `notify_watering` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plants`
--

LOCK TABLES `plants` WRITE;
/*!40000 ALTER TABLE `plants` DISABLE KEYS */;
INSERT INTO `plants` VALUES (2,839767279,'Трандесканция',NULL,NULL,NULL,1,'2025-11-02',NULL,'2025-10-31 21:44:46',0),(6,839767279,'Монстера',12.00,'Рыхлая','В тени',4,'2025-10-30','Красавица','2025-11-01 10:07:39',0),(7,839767279,'Сциндапсус',32.00,'Дренированная','Прямые солнечные лучи',1,'2025-10-31','Милашка','2025-11-01 14:38:21',0),(8,839767279,'Тилландсия',NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-01 14:40:33',0),(9,839767279,'Кактус',3.00,NULL,NULL,10,'2025-10-10',NULL,'2025-11-01 14:45:45',0),(10,839767279,'Сингониум',NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-01 15:01:16',0),(11,839767279,'Роза',NULL,NULL,NULL,NULL,NULL,NULL,'2025-11-02 17:12:30',0);
/*!40000 ALTER TABLE `plants` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-04  0:50:13
