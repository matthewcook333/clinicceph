package edu.hmc.cs.ntpstats.parser
import io.Source
import spray.json._

case class LogLine(fields: List[String])
case class LogFile(lines: List[LogLine])
object LogFile {
  def apply(file: Source): LogFile = {
    new LogFile(file.getLines.map(x => // required because using _ scala thinks it's an int??
        LogLine(x.split("\\s+").toList)).toList
    )
  }
  
  def apply(filePath: String): LogFile = apply(Source.fromFile(filePath))
}

case class FieldEntry(date: String, time: String, Value: String)

object FieldEntryJsonProtocol extends DefaultJsonProtocol {
  implicit val fieldFormat = jsonFormat3(FieldEntry)
}

case class NTPStatsFiles(peerstats: LogFile, loopstats: LogFile, rawstats: LogFile)

object NTPStatsFiles {
  def apply(peerPath: String, loopPath: String, rawPath: String): NTPStatsFiles = {
    new NTPStatsFiles(LogFile(peerPath), LogFile(loopPath), LogFile(rawPath))
  }
}

case class QueriedFields(fields: List[Int])
object LoopStats
object RawStats
object PeerStats