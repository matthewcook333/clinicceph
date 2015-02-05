package edu.hmc.cs.ntpstats.parser
import spray.json._
import FieldEntryJsonProtocol._

/**
  *  @TODO: Handle fields in multiple files.
  */


object Field extends Enumeration {
  type Field = Value

  // loopstats fields
  val Date = Value("date")
  val TimePastMidnight = Value("time past midnight")
  val ClockOffset = Value("clock offset")
  val FreqOffset = Value("frequency offset")
  val RmsJitter = Value("RMS jitter")
  val RmsFreq = Value("RMS frequency")
  val LoopTimeConstant = Value("clock discipline loop time constant")
  
  // Fields we hit loopstats for
  val LoopStatsQueryFields = List(Date, TimePastMidnight, ClockOffset, FreqOffset, 
      RmsJitter, RmsFreq, LoopTimeConstant)

  // not-already-declared-fields for peerstats
  val SourceAddr = Value("source address")
  val StatusWord = Value("status word")
  val RoundtripDelay = Value("roundtrip delay")
  val Dispersion = Value("dispersion")
  
  // Fields we hit peerstats for
  val PeerStatsQueryFields = List(SourceAddr, StatusWord, RoundtripDelay, Dispersion)

  // not-already-declared-fields for rawstats
  val DestAddr = Value("destination address")
  val OriginTS = Value("origin timestamp")
  val ReceiveTS = Value("receive timestamp")
  val TransmitTS = Value("transmit timestamp")
  val DestTS = Value("destination timestamp")
  val LeapWarning = Value("leap warning indicator")
  val Version = Value("ntp version")
  val Mode = Value("mode")
  val Stratum = Value("stratum")
  val Poll = Value("poll")
  val Precision = Value("precision")
  val RefClockRoundtrip = Value("total roundtrip delay to the primary reference clock")
  val RefClockDispersion = Value("total dispersion to the primary reference clock")
  val RefId = Value("refid, association ID")
  
  // Fields we hit rawstats for
  val RawStatsQueryFields = List(DestAddr, OriginTS, ReceiveTS, TransmitTS, DestTS,
      LeapWarning,Version,Mode,Stratum,Poll,Precision,RefClockRoundtrip,
      RefClockDispersion, RefId)


  /**
    * May Odersky have mercy on my soul.
    * @return The field value corresponding to a given number used to form a query
    */
  def numToFieldValue(num: Int) = num match {
    case 1  => Date
    case 2  => TimePastMidnight
    case 3  => ClockOffset
    case 4  => FreqOffset
    case 5  => RmsJitter
    case 6  => RmsFreq
    case 7  => LoopTimeConstant
    case 8  => SourceAddr
    case 9  => StatusWord
    case 10 => RoundtripDelay
    case 11 => Dispersion
    case 12 => DestAddr
    case 13 => OriginTS
    case 14 => ReceiveTS
    case 15 => TransmitTS
    case 16 => DestTS
    case 17 => LeapWarning
    case 18 => Version
    case 19 => Mode
    case 20 => Stratum
    case 21 => Poll
    case 22 => Precision
    case 23 => RefClockRoundtrip
    case 24 => RefClockDispersion
    case 25 => RefId
  }

  /**
    * May Odersky have mercy on my soul
    * @return The numerical position of the field in the file we look it up in.
    */
  def fieldNameToFieldNum(field: Field.Value) = field match {
    case Date               => 0
    case TimePastMidnight   => 1
    case ClockOffset        => 2
    case FreqOffset         => 3
    case RmsJitter          => 4
    case RmsFreq            => 5
    case LoopTimeConstant   => 6
    case SourceAddr         => 2
    case StatusWord         => 3
    case RoundtripDelay     => 5
    case Dispersion         => 6
    case DestAddr           => 3
    case OriginTS           => 4
    case ReceiveTS          => 5
    case TransmitTS         => 6
    case DestTS             => 7
    case LeapWarning        => 8
    case Version            => 9
    case Mode               => 10
    case Stratum            => 11
    case Poll               => 12
    case Precision          => 13
    case RefClockRoundtrip  => 14
    case RefClockDispersion => 15
    case RefId              => 16
  }
  
  def fieldToFile(field: Field.Value) = {
    if(LoopStatsQueryFields.contains(field)) {
      LoopStats
    } else if(PeerStatsQueryFields.contains(field)) {
      PeerStats
    }
    else {
     RawStats
    }
  }
}

class QueryEngine(files: NTPStatsFiles) {
	def query(fields: List[Field.Value]): JsValue = {
	  val loopFields = fields.filter(Field.fieldToFile(_) == LoopStats)
	  val peerFields = fields.filter(Field.fieldToFile(_) == PeerStats)
	  val rawFields  = fields.filter(Field.fieldToFile(_) == RawStats)
	  
	  import QueryEngine.getFields
	  (getFields(files.loopstats, loopFields) ++ 
	  	getFields(files.peerstats, peerFields) ++
	  	getFields(files.rawstats, rawFields)).toJson
	}
}

object QueryEngine {
  def apply(files: NTPStatsFiles): QueryEngine = new QueryEngine(files)
  
  /**
    * @return list of tuples of the format (date, time after midnight, fieldValue)
    */
  def getFields(line: LogLine, fields: List[Int]): List[FieldEntry] =
    fields.map(x => FieldEntry(line.fields(0), line.fields(1), line.fields(x)))

  /**
    * @return List of lists, where each sublist has all the entries for a given field
    */
  def getFields(log: LogFile, fields: List[Field.Value]): List[List[FieldEntry]] = {
    val listOfEntries = log.lines.map(
      getFields(_, fields.map(Field.fieldNameToFieldNum(_)))
    )

    listOfEntries.transpose // Switches to list of numbers for each field
  }
}

object Runner extends App {
  val usage = """
    Usage: ./logparser loopstats_path peerstats_path rawstats_path f1 f2 f3 ...   
    where f1, f2, f3, etc are numbers between 1 and 25. 
    
    Field correspondence to numbers:
	  Date               => 1
      TimePastMidnight   => 2
      ClockOffset        => 3
      FreqOffset         => 4
      RmsJitter          => 5
      RmsFreq            => 6
      LoopTimeConstant   => 7
      SourceAddr         => 8
      StatusWord         => 9
      RoundtripDelay     => 10
      Dispersion         => 11
      DestAddr           => 12
      OriginTS           => 13
      ReceiveTS          => 14
      TransmitTS         => 15
      DestTS             => 16
      LeapWarning        => 17
      Version            => 18
      Mode               => 19
      Stratum            => 20
      Poll               => 21
	  Precision          => 22
      RefClockRoundtrip  => 23
      RefClockDispersion => 24
      RefId              => 25
    """
  
  if(args.length == 0) {
    println(usage)
  } else {
	  val loopPath = args(0)
	  val peerPath = args(1)
	  val rawPath = args(2)
  
	  val engine = QueryEngine(NTPStatsFiles(loopPath, peerPath, rawPath))
	  try {
		  val queryFields = args.drop(3).map(_.toInt)
		  engine.query(args.drop(3).map(x => Field.numToFieldValue(x.toInt)).toList)
	  } catch {
	    case _: java.lang.NumberFormatException => 
	      System.err.println("Error, nonnumeric field argument."); System.out.println(usage)
	  }
  }
}