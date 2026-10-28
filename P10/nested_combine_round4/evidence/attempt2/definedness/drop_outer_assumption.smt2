; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun p () (_ BitVec 1))
(declare-fun q () (_ BitVec 1))
(assert
 (let (($x10 (and true true (and (distinct p (_ bv0 1)) true))))
(let (($x32 (and $x10 true (and (distinct q (_ bv0 1)) true))))
(or (and (distinct $x32 $x10) true) (and $x32 $x10 (and (distinct ((_ extract 7 0) ((_ extract 7 0) a)) ((_ extract 7 0) a)) true))))))
(check-sat)
