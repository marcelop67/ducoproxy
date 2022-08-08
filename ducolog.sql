DROP TABLE `box`;
DROP TABLE `sensors`;

CREATE TABLE `box` (
  `box_logid` int NOT NULL AUTO_INCREMENT,
  `logtime` datetime NOT NULL,
  `uptime` int DEFAULT NULL,
  `mode` varchar(6) DEFAULT NULL,
  `state` varchar(6) DEFAULT NULL,
  `level` tinyint DEFAULT NULL,
  `cntdwn` smallint DEFAULT NULL,
  `temp_oda` float DEFAULT NULL,
  `temp_sup` float DEFAULT NULL,
  `temp_eta` float DEFAULT NULL,
  `temp_eha` float DEFAULT NULL,
  `remainfilter_days` smallint DEFAULT NULL,
  `remainfilter_percent` smallint DEFAULT NULL,
  `bypass` tinyint DEFAULT NULL,
  `frost` tinyint(1) DEFAULT NULL,
  `power` float DEFAULT NULL,
  `has_control` varchar(14) DEFAULT NULL,
  PRIMARY KEY (`box_logid`),
  INDEX (`logtime` DESC),
  INDEX (`box_logid` DESC)
) ENGINE=InnoDB;

CREATE TABLE `sensors` (
  `sensors_logid` int NOT NULL AUTO_INCREMENT,
  `logtime` datetime NOT NULL,
  `nid` tinyint NOT NULL,
  `location` varchar(14) DEFAULT NULL,
  `devtype` varchar(6) DEFAULT NULL,
  `temp` float DEFAULT NULL,
  `co2` float DEFAULT NULL,
  `rh` float DEFAULT NULL,
  `target` float DEFAULT NULL,
  `box_logid` int NOT NULL,
  PRIMARY KEY (`sensors_logid`),
  INDEX (`logtime` DESC),
  INDEX (`box_logid` DESC)
) ENGINE=InnoDB;
