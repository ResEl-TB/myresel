-- phpMyAdmin SQL Dump
-- version 3.4.11.1deb2+deb7u6
-- http://www.phpmyadmin.net
--
-- Host: maia.adm.resel.fr
-- Generation Time: Nov 26, 2016 at 01:57 PM
-- Server version: 5.5.53
-- PHP Version: 5.4.45-0+deb7u5

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `qos`
--

-- --------------------------------------------------------

--
-- Table structure for table `classes`
--

DROP TABLE IF EXISTS `classes`;
CREATE TABLE IF NOT EXISTS `classes` (
  `site` varchar(32) NOT NULL,
  `index` int(11) NOT NULL,
  `way` enum('down','up') NOT NULL,
  `flow` enum('clean','dirty') NOT NULL,
  `tcindex` int(11) NOT NULL,
  `name` varchar(16) NOT NULL,
  `fixed` tinyint(1) NOT NULL,
  `limit` bigint(11) NOT NULL,
  `rate` int(11) NOT NULL,
  `ceil` int(11) NOT NULL,
  `quantum` int(11) NOT NULL,
  `users` int(11) NOT NULL,
  `users_active` int(11) NOT NULL,
  `last_rate` int(11) NOT NULL,
  `rule` varchar(16) NOT NULL,
  PRIMARY KEY (`index`,`way`,`flow`,`site`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `classes_history`
--

DROP TABLE IF EXISTS `classes_history`;
CREATE TABLE IF NOT EXISTS `classes_history` (
  `site` varchar(32) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `index` int(11) NOT NULL,
  `way` enum('down','up') NOT NULL,
  `flow` enum('clean','dirty') NOT NULL,
  `name` varchar(16) NOT NULL,
  `fixed` tinyint(1) NOT NULL,
  `limit` bigint(11) NOT NULL,
  `rate` int(11) NOT NULL,
  `ceil` int(11) NOT NULL,
  `quantum` int(11) NOT NULL,
  `users` int(11) NOT NULL,
  `users_active` int(11) NOT NULL,
  `last_rate` int(11) NOT NULL,
  `rule` varchar(16) NOT NULL,
  PRIMARY KEY (`index`,`way`,`flow`,`site`,`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `lastentry`
--

DROP TABLE IF EXISTS `lastentry`;
CREATE TABLE IF NOT EXISTS `lastentry` (
  `site` varchar(32) NOT NULL,
  `name` varchar(32) NOT NULL,
  `value` int(11) NOT NULL,
  PRIMARY KEY (`name`,`site`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `people`
--

DROP TABLE IF EXISTS `people`;
CREATE TABLE IF NOT EXISTS `people` (
  `site` varchar(32) NOT NULL,
  `cn` varchar(128) NOT NULL,
  `last_entry` int(11) NOT NULL,
  PRIMARY KEY (`cn`,`site`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `people_data`
--

DROP TABLE IF EXISTS `people_data`;
CREATE TABLE IF NOT EXISTS `people_data` (
  `site` varchar(32) NOT NULL,
  `cn` varchar(128) NOT NULL,
  `uid` varchar(16) NOT NULL,
  `way` enum('down','up') NOT NULL,
  `flow` enum('clean','dirty') NOT NULL,
  `group` int(11) NOT NULL,
  `amount` bigint(11) NOT NULL,
  `amount_ponderated` bigint(11) NOT NULL,
  `last_rate` int(11) NOT NULL,
  PRIMARY KEY (`cn`,`way`,`flow`,`site`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `people_history`
--

DROP TABLE IF EXISTS `people_history`;
CREATE TABLE IF NOT EXISTS `people_history` (
  `site` varchar(32) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `cn` varchar(128) NOT NULL,
  `uid` varchar(16) NOT NULL,
  `way` enum('down','up') NOT NULL,
  `flow` enum('clean','dirty') NOT NULL,
  `group` int(11) NOT NULL,
  `amount` bigint(11) NOT NULL,
  `amount_ponderated` bigint(11) NOT NULL,
  `duration` int(11) NOT NULL,
  PRIMARY KEY (`cn`,`way`,`flow`,`site`,`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
